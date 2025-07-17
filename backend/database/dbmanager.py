import os
import glob
import time

from typing import List, Tuple, Optional, Union, Set

import pandas as pd
from storage.HeapFile import HeapFile
from storage.Record import Record
from indexing.SequentialIndex import SequentialIndex
from indexing.ExtendibleHashIndex import ExtendibleHashIndex
from indexing.BPlusTreeIndex import BPlusTreeIndex, BPlusTreeIndexWrapper
from indexing.IndexRecord import IndexRecord, re_string
from indexing.RTreeIndex import RTreeIndex
from indexing.Spimi import SPIMIIndexer
from indexing.SpimiAudio import SpimiAudioIndexer
from fancytypes.column_types import IndexType, ColumnType
from statement import (
    BoolExpression,
    ColumnExpression,
    CreateColumnDefinition,
    FloatExpression,
    IntExpression,
    Point2DExpression,
    Point3DExpression,
    StringExpression,
    ValueExpression,
)
from fancytypes.schema import SchemaType
from fancytypes.column_types import OperationType
from database import build_acoustic_model
from storage.Sound import Sound
from storage.HistogramFile import HistogramFile

from database import build_acoustic_model, search_text, knn_search, knn_search_index

from logger import Logger


class DBManager:
    _instance = None
    base_dir = os.path.dirname(os.path.abspath(__file__))
    tables_dir = os.path.join(base_dir, "tables")
    os.makedirs(tables_dir, exist_ok=True)

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(DBManager, cls).__new__(cls, *args, **kwargs)
        return cls._instance

    def __init__(self):
        if hasattr(self, "_initialized") and self._initialized:  # gpt
            return
        self._initialized = True

    # region Helper methods
    @staticmethod
    def table_path(table_name: str) -> str:
        """Devuelve la ruta absoluta (sin extensión) de la tabla."""
        return os.path.join(DBManager.tables_dir, table_name)
        # region Helper methods

    @staticmethod
    def check_table_exists(table_name: str) -> bool:
        return os.path.exists(DBManager.table_path(table_name) + ".dat") and os.path.exists(
            DBManager.table_path(table_name) + ".schema.json"
        )

    @staticmethod
    def verify_table_exists(table_name: str) -> None:
        if not DBManager.check_table_exists(table_name):
            raise FileNotFoundError(f"Table {table_name} does not exist")

    @staticmethod
    def verify_table_not_exists(table_name: str) -> None:
        if DBManager.check_table_exists(table_name):
            raise FileExistsError(f"Table {table_name} already exists")

    @staticmethod
    def get_table_schema(table_name: str):
        DBManager.verify_table_exists(table_name)
        schema_path = DBManager.table_path(table_name) + ".schema.json"
        heapfile = HeapFile(DBManager.table_path(table_name))
        return heapfile.schema

    @staticmethod
    def get_table_heap(table_name: str) -> HeapFile:
        DBManager.verify_table_exists(table_name)
        return HeapFile(DBManager.table_path(table_name))

    @staticmethod
    def get_field_format(table_name: str, field_name: str) -> str:
        schema = DBManager.get_table_schema(table_name)
        for name, format in schema:
            if name == field_name:
                return format
        raise ValueError(f"Field {field_name} not found in table {table_name}")

    @staticmethod
    def get_column_position(table_name: str, field_name: str) -> int:
        schema = DBManager.get_table_schema(table_name)
        i = 0
        for name, format in schema:
            if name == field_name:
                return i
            i += 1
        raise ValueError(f"Field {field_name} not found in table {table_name}")

    @staticmethod
    def get_field_type(table_name: str, field_name: str) -> ColumnType:
        format = DBManager.get_field_format(table_name, field_name)
        match format:
            case "i":
                return ColumnType.INT
            case "f":
                return ColumnType.FLOAT
            case "?":
                return ColumnType.BOOL
            case "2f":
                return ColumnType.POINT2D
            case "3f":
                return ColumnType.POINT3D
            case _ if re_string.fullmatch(format):
                return ColumnType.VARCHAR
            case "text":
                return ColumnType.TEXT
            case "sound":
                return ColumnType.SOUND
            case _:
                raise ValueError(f"Unknown format '{format}' for field '{field_name}' in table '{table_name}'")

    @staticmethod
    def type_to_format(column_type: ColumnType, varchar_length: int = 0) -> str:
        match column_type:
            case ColumnType.INT:
                return "i"
            case ColumnType.FLOAT:
                return "f"
            case ColumnType.VARCHAR:
                return f"{varchar_length}s"
            case ColumnType.BOOL:
                return "?"
            case ColumnType.POINT2D:
                return "2f"
            case ColumnType.POINT3D:
                return "3f"
            case ColumnType.TEXT:
                return "text"
            case ColumnType.SOUND:
                return "sound"
            case _:
                raise ValueError(f"Unsupported column type: {column_type}")

    @staticmethod
    def validate_simplecomparison(
        table_name: str,
        left_value: ValueExpression,
        op: OperationType,
        right_value: ValueExpression,
    ) -> bool:
        left_type = None
        right_type = None

        exp_to_type = {
            IntExpression: ColumnType.INT,
            FloatExpression: ColumnType.FLOAT,
            BoolExpression: ColumnType.BOOL,
            StringExpression: ColumnType.VARCHAR,
            Point2DExpression: ColumnType.POINT2D,
            Point3DExpression: ColumnType.POINT3D,
        }

        if type(left_value) is ColumnExpression:
            left_value = (ColumnExpression)(left_value)
            DBManager.verify_table_exists(left_value.column_name)
            field_name = left_value.column_name
            left_type: ColumnType = DBManager.get_field_type(table_name, field_name)
        else:
            left_type = exp_to_type.get(type(left_value))

        if type(right_value) is ColumnExpression:
            right_value = (ColumnExpression)(right_value)
            DBManager.verify_table_exists(right_value.column_name)
            field_name = right_value.column_name
            right_type: ColumnType = DBManager.get_field_type(table_name, field_name)
        else:
            right_type = exp_to_type.get(type(right_value))

        # ATAT: only TEXT @@ VARCHAR
        if op == OperationType.ATAT:
            return left_type == ColumnType.TEXT and right_type == ColumnType.VARCHAR

        # poins equality only
        if left_type in (ColumnType.POINT2D, ColumnType.POINT3D) or right_type in (
            ColumnType.POINT2D,
            ColumnType.POINT3D,
        ):
            if op != OperationType.EQUAL:
                return False
            return left_type == right_type and left_type in (
                ColumnType.POINT2D,
                ColumnType.POINT3D,
            )

        # Equality: any two equal types, plus int/float interchangeably, plus VARCHAR/TEXT
        if op == OperationType.EQUAL or op == OperationType.NOT_EQUAL:
            if left_type == right_type:
                return True
            if left_type in (ColumnType.INT, ColumnType.FLOAT) and right_type in (
                ColumnType.INT,
                ColumnType.FLOAT,
            ):
                return True
            if (left_type, right_type) in [
                (ColumnType.VARCHAR, ColumnType.TEXT),
                (ColumnType.TEXT, ColumnType.VARCHAR),
            ]:
                return True
            return False

        return left_type == right_type

    # region Index creation
    @staticmethod
    def create_seq_idx(table_name: str, field_name: str) -> None:
        type = DBManager.get_field_type(table_name, field_name)
        if type not in (ColumnType.INT, ColumnType.FLOAT, ColumnType.VARCHAR):
            raise ValueError(f"Unsupported index for field {field_name} of type {type} in table {table_name}.")
        path = DBManager.table_path(table_name)
        SequentialIndex.build_index(path, HeapFile(path).extract_index, field_name)

    @staticmethod
    def create_hash_idx(table_name: str, field_name: str) -> None:
        type = DBManager.get_field_type(table_name, field_name)
        if type not in (ColumnType.INT, ColumnType.VARCHAR):
            raise ValueError(f"Unsupported hash index for field {field_name} of type {type} in table {table_name}.")
        path = DBManager.table_path(table_name)
        ExtendibleHashIndex.build_index(path, HeapFile(path).extract_index, field_name)

    @staticmethod
    def create_btree_idx(table_name: str, field_name: str) -> None:
        type = DBManager.get_field_type(table_name, field_name)
        if type not in (ColumnType.INT, ColumnType.FLOAT, ColumnType.VARCHAR):
            raise ValueError(f"Índice B+Tree no soportado para el campo {field_name} de tipo {type} en la tabla {table_name}.")
        path = DBManager.table_path(table_name)
        BPlusTreeIndex.build_index(path, HeapFile(path).extract_index, field_name)

    @staticmethod
    def create_rtree_idx(table_name: str, field_name: str) -> None:
        type = DBManager.get_field_type(table_name, field_name)
        if type not in (ColumnType.POINT2D, ColumnType.POINT3D):
            raise ValueError(f"Índice R-Tree no soportado para el campo {field_name} de tipo {type} en la tabla {table_name}.")
        path = DBManager.table_path(table_name)
        RTreeIndex.build_index(path, HeapFile(path).extract_index, field_name)

    @staticmethod
    def create_spimi_idx(table_name: str) -> None:
        SPIMIIndexer().build_index(table_name)

    @staticmethod
    def create_spimi_audio_idx(table_name: str, field_name) -> None:
        build_acoustic_model(DBManager.table_path(table_name), field_name, 1)
        SpimiAudioIndexer(
            DBManager.table_path,
            field_name,
            index_table_name=f"{table_name}.{field_name}",
        ).build_index(table_name)

    # region Index verification
    @staticmethod
    def check_seq_idx(table_name: str, field: str) -> bool:
        table_path = DBManager.table_path(table_name)
        index_path = f"{table_path}.{field}.seq.idx"
        return os.path.exists(index_path)

    @staticmethod
    def check_hash_idx(table_name: str, field: str) -> bool:
        table_path = DBManager.table_path(table_name)
        index_paths = (f"{table_path}.{field}.btree.{ext}" for ext in ("idx", "db", "tree"))
        return all(os.path.exists(index_path) for index_path in index_paths)

    @staticmethod
    def check_btree_idx(table_name: str, field: str) -> bool:
        table_path = DBManager.table_path(table_name)
        index_path = f"{table_path}.{field}.btree.idx"
        return os.path.exists(index_path)

    @staticmethod
    def check_rtree_idx(table_name: str, field: str) -> bool:
        table_path = DBManager.table_path(table_name)
        index_paths = (f"{table_path}.{field}.rtree.{ext}" for ext in ("idx", "dat"))
        return all(os.path.exists(index_path) for index_path in index_paths)

    # region Index deletion
    @staticmethod
    def drop_seq_idx(table_name: str, field) -> None:
        table_path = DBManager.table_path(table_name)
        index_path = f"{table_path}.{field}.seq.idx"
        if not os.path.exists(index_path):
            raise FileNotFoundError(f"Índice secuencial para {field} en la tabla {table_name} no existe.")
        os.remove(index_path)
        Logger.log_dbmanager(f"Índice secuencial para {field} en la tabla {table_name} eliminado con éxito.")

    @staticmethod
    def drop_hash_idx(table_name: str, field) -> None:
        table_path = DBManager.table_path(table_name)
        index_paths = (f"{table_path}.{field}.btree.{ext}" for ext in ("idx", "db", "tree"))
        for index_path in index_paths:
            if not os.path.exists(index_path):
                raise FileNotFoundError(f"Índice Hash para {field} en la tabla {table_name} no existe.")
            os.remove(index_path)
        Logger.log_dbmanager(f"Índice hash para {field} en la tabla {table_name} eliminado con éxito.")

    @staticmethod
    def drop_btree_idx(table_name: str, field) -> None:
        table_path = DBManager.table_path(table_name)
        index_path = f"{table_path}.{field}.btree.idx"
        if not os.path.exists(index_path):
            raise FileNotFoundError(f"Índice B+Tree para {field} en la tabla {table_name} no existe.")
        os.remove(index_path)
        Logger.log_dbmanager(f"Índice B+Tree para {field} en la tabla {table_name} eliminado con éxito.")

    @staticmethod
    def drop_rtree_idx(table_name: str, field) -> None:
        table_path = DBManager.table_path(table_name)
        index_paths = (f"{table_path}.{field}.rtree.{ext}" for ext in ("idx", "dat"))
        for index_path in index_paths:
            if not os.path.exists(index_path):
                raise FileNotFoundError(f"Índice R-Tree para {field} en la tabla {table_name} no existe.")
            os.remove(index_path)
        Logger.log_dbmanager(f"Índice R-Tree para {field} en la tabla {table_name} eliminado con éxito.")

    @staticmethod
    def drop_all_indexes_field(table_name: str, field: str) -> None:
        if DBManager.check_seq_idx(table_name, field):
            DBManager.drop_seq_idx(table_name, field)
        if DBManager.check_hash_idx(table_name, field):
            DBManager.drop_hash_idx(table_name, field)
        if DBManager.check_btree_idx(table_name, field):
            DBManager.drop_btree_idx(table_name, field)
        if DBManager.check_rtree_idx(table_name, field):
            DBManager.drop_rtree_idx(table_name, field)

    @staticmethod
    def drop_all_indexes_table(table_name: str) -> None:
        table_path = DBManager.table_path(table_name)
        fields = [name for name, _ in DBManager.get_table_schema(table_name)]
        for field in fields:
            DBManager.drop_all_indexes_field(table_name, field)

    # region Index update
    @staticmethod
    def update_secondary_indexes(table_path: str, record: Record, offset: int) -> None:
        schema = record.schema
        for idx_file in glob.glob(f"{table_path}.*.*.idx"):
            parts = os.path.basename(idx_file).split(".")
            if len(parts) < 4:
                continue
            field_name, idx_type = parts[1], parts[2]
            field_type = next((fmt for name, fmt in schema if name == field_name), None)
            if field_type is None:
                continue
            value = record.values[[n for n, _ in schema].index(field_name)]
            idx_rec = IndexRecord(field_type, value, offset)
            if idx_type == "seq":
                SequentialIndex(table_path, field_name).insert_record(idx_rec)
            elif idx_type == "hash":
                ExtendibleHashIndex(table_path, field_name).insert_record(idx_rec)
            elif idx_type == "btree":
                start = time.time()
                BPlusTreeIndexWrapper(table_path, field_name).insert_record(idx_rec)
                end = time.time()
            elif idx_type == "rtree":
                RTreeIndex(table_path, field_name).insert_record(idx_rec)

    @staticmethod
    def remove_from_secondary_indexes(table_path: str, record: Optional[Record], offset: int) -> None:
        if not record:
            return
        schema = record.schema
        for index_file in glob.glob(f"{table_path}.*.*.idx"):
            parts = os.path.basename(index_file).split(".")
            if len(parts) < 4:
                continue
            field_name, idx_type = parts[1], parts[2]
            field_type = next((fmt for name, fmt in schema if name == field_name), None)
            if field_type is None:
                continue
            value = record.values[[n for n, _ in schema].index(field_name)]
            if idx_type == "seq":
                SequentialIndex(table_path, field_name).delete_record(value, offset)
            elif idx_type == "hash":
                ExtendibleHashIndex(table_path, field_name).delete_record(value, offset)
            elif idx_type == "btree":
                BPlusTreeIndexWrapper(table_path, field_name).delete_record(value, offset)
            elif idx_type == "rtree":
                RTreeIndex(table_path, field_name).delete_record(value, offset)

    # region Index search
    @staticmethod
    def search_by_field(table_name: str, field_name: str, value):
        return HeapFile(DBManager.table_path(table_name)).search_by_field(field_name, value)

    @staticmethod
    def search_seq_idx(table_name: str, field_name: str, value: Union[int, float, str]) -> Set[int]:
        table_path = DBManager.table_path(table_name)
        idx = SequentialIndex(table_path, field_name)
        return {r.offset for r in idx.search_record(value)}

    @staticmethod
    def search_seq_idx_range(
        table_name: str,
        field_name: str,
        range: Tuple[Union[int, float, str], Union[int, float, str]],
    ) -> Set[int]:
        table_path = DBManager.table_path(table_name)
        idx = SequentialIndex(table_path, field_name)
        return {r.offset for r in idx.search_range(range[0], range[1])}

    @staticmethod
    def search_hash_idx(table_name: str, field_name: str, value: Union[int, str]) -> Set[int]:
        table_path = DBManager.table_path(table_name)
        idx = ExtendibleHashIndex(table_path, field_name)
        return {r.offset for r in idx.search_record(value)}

    @staticmethod
    def search_btree_idx(table_name: str, field_name: str, field_value) -> Set[int]:
        table_path = DBManager.table_path(table_name)
        idx = BPlusTreeIndexWrapper(table_path, field_name)
        return set(idx.search(field_value))

    @staticmethod
    def search_btree_idx_range(
        table_name: str,
        field_name: str,
        range: Tuple[Union[int, float, str], Union[int, float, str]],
    ) -> Set[int]:
        table_path = DBManager.table_path(table_name)
        idx = BPlusTreeIndexWrapper(table_path, field_name)
        return set(idx.range_search(range[0], range[1]))

    @staticmethod
    def search_rtree_record(table_name: str, field_name: str, point: Tuple[Union[int, float], ...]) -> Set[int]:
        table_path = DBManager.table_path(table_name)
        idx = RTreeIndex(table_path, field_name)
        return {r.offset for r in idx.search_record(point)}

    @staticmethod
    def search_rtree_bounds(
        table_name: str,
        field_name: str,
        bounds: Tuple[Tuple[Union[int, float], ...], Tuple[Union[int, float], ...]],
    ) -> Set[int]:
        table_path = DBManager.table_path(table_name)
        idx = RTreeIndex(table_path, field_name)
        return {r.offset for r in idx.search_bounds(bounds[0], bounds[1])}

    @staticmethod
    def search_rtree_radius(
        table_name: str,
        field_name: str,
        bounds: Tuple[Tuple[Union[int, float], ...], float],
    ) -> Set[int]:
        table_path = DBManager.table_path(table_name)
        idx = RTreeIndex(table_path, field_name)
        return {r.offset for r in idx.search_radius(bounds[0], bounds[1])}

    @staticmethod
    def search_rtree_knn(
        table_name: str,
        field_name: str,
        bounds: Tuple[Tuple[Union[int, float], ...], int],
    ) -> Set[int]:
        table_path = DBManager.table_path(table_name)
        idx = RTreeIndex(table_path, field_name)
        return {r.offset for r in idx.search_knn(bounds[0], bounds[1])}

    # region Main methods
    @staticmethod
    def create_table_aux(
        table_name: str,
        schema: List[Tuple[str, str]],
        primary_key: Optional[str] = None,
    ) -> None:
        HeapFile.build_file(DBManager.table_path(table_name), schema, primary_key)  # "text" might be sent here
        Logger.log_dbmanager(f"Tabla {table_name} creada con éxito.")

    @staticmethod
    def drop_table_aux(table_name: str) -> None:
        DBManager.drop_all_indexes_table(table_name)
        table_path = DBManager.table_path(table_name)
        os.remove(f"{table_path}.dat")
        os.remove(f"{table_path}.schema.json")

    @staticmethod
    def insert_record(table_name: str, record: Record) -> int:
        table_path = DBManager.table_path(table_name)
        heap = HeapFile(table_path)

        values = list(record.values)
        for i, (field_name, field_type) in enumerate(record.schema):
            if field_type.upper() == "SOUND":
                sound_path = values[i]
                if isinstance(sound_path, str):
                    sound_file = Sound(DBManager.table_path(table_name), field_name)
                    sound_offset = sound_file.insert(sound_path)
                    values[i] = (sound_offset, -1)  # -1 for histogram offset
        record.values = list(values)
        offset = heap.insert_record(record)
        DBManager.update_secondary_indexes(table_path, record, offset)
        return offset

    @staticmethod
    def delete_record(table_name: str, pk_value):
        table_path = DBManager.table_path(table_name)
        heap = HeapFile(table_path)
        ok, offset, old_rec = heap.delete_by_pk(pk_value)
        if not ok:
            return False
        DBManager.remove_from_secondary_indexes(table_path, old_rec, offset)
        return True

    # region Parser helpers

    def create_table(self, table_name: str, columns: list[CreateColumnDefinition]) -> None:
        DBManager.verify_table_not_exists(table_name)
        schema: SchemaType = []
        pk: str = ""
        for column in columns:
            format: str = DBManager.type_to_format(column.column_type, column.varchar_length)
            if column.is_pk:
                if pk:
                    raise ValueError(f"Multiple primary keys defined for table '{table_name}'.")
                pk = column.column_name
            schema.append((column.column_name, format))
        for field_name, field_type in schema:
            if field_type.upper() == "SOUND":
                HistogramFile.build_file(DBManager.table_path(table_name), field_name)
        Logger.log_dbmanager(f"Tabla '{table_name}' creada con éxito.")
        DBManager.create_table_aux(table_name, schema, pk)

    def drop_table(self, table_name: str) -> None:
        if not DBManager.check_table_exists(table_name):
            raise ValueError(f"La tabla '{table_name}' no existe.")
        DBManager.drop_table_aux(table_name)

    def create_index(self, table_name: str, field_name: str, index_type: IndexType) -> None:
        DBManager.verify_table_exists(table_name)
        match index_type:
            case IndexType.SEQUENTIAL:
                DBManager.create_seq_idx(table_name, field_name)
            case IndexType.EXTENDIBLEHASH:
                DBManager.create_hash_idx(table_name, field_name)
            case IndexType.BPLUSTREE:
                DBManager.create_btree_idx(table_name, field_name)
            case IndexType.RTREE:
                DBManager.create_rtree_idx(table_name, field_name)
            case IndexType.SPIMI:
                DBManager.create_spimi_idx(table_name)
            case IndexType.SPIMIAUDIO:
                DBManager.create_spimi_audio_idx(table_name, field_name)
            case _:
                raise ValueError(f"Unknown index type: {index_type}")

    def drop_index(self, table_name: str, field_name: str, index_type: IndexType) -> None:
        DBManager.verify_table_exists(table_name)
        match index_type:
            case IndexType.SEQUENTIAL:
                DBManager.drop_seq_idx(table_name, field_name)
            case IndexType.EXTENDIBLEHASH:
                DBManager.drop_hash_idx(table_name, field_name)
            case IndexType.BPLUSTREE:
                DBManager.drop_btree_idx(table_name, field_name)
            case IndexType.RTREE:
                DBManager.drop_rtree_idx(table_name, field_name)
            case _:
                raise ValueError(f"Unknown index type: {index_type}")

    def insert(self, table_name: str, columns: list[str], values: list) -> None:
        DBManager.verify_table_exists(table_name)
        if len(columns) != len(values):
            raise ValueError("Column names and values length mismatch.")
        schema: SchemaType = DBManager.get_table_schema(table_name)
        schema_dict: dict = dict(schema)
        for column, value in zip(columns, values):
            if column not in schema_dict:
                raise ValueError(f"Column '{column}' does not exist in table '{table_name}'.")
            column_type = DBManager.get_field_type(table_name, column)
            type_map: dict = {
                ColumnType.INT: [int],
                ColumnType.FLOAT: [float, int],
                ColumnType.BOOL: [bool],
                ColumnType.POINT2D: [tuple[float, float]],
                ColumnType.POINT3D: [tuple[float, float, float]],
                ColumnType.VARCHAR: [str],
                ColumnType.TEXT: [str],
                ColumnType.SOUND: [str],
            }
            if type(value) not in type_map[column_type]:
                raise TypeError(f"Value for column '{column}' must be of type {column_type}, got {type(value)}.")

        # the values array might not be in the correct order for schema
        value_dict = dict(zip(columns, values, strict=True))
        Logger.log_dbmanager(value_dict)
        ordered_values = []
        for name, fmt in schema:
            if name in value_dict:
                ordered_values.append(value_dict[name])
            else:
                raise ValueError(f"Column '{name}' is missing in the insert statement. NULL is not supported yet.")
        DBManager.insert_record(table_name, Record(schema, ordered_values))

    def fetch_condition_offsets(self, table_name: str, left_value, op: OperationType, right_value, k: int) -> set[int]:
        Logger.log_debug(f"LEFT SIDE TYPE: {type(left_value)}")
        Logger.log_debug(f"RIGHT SIDE TYPE: {type(right_value)}")

        # I AM NOT VALIDATING TYPES I AM NOT VALIDATING TYPES, I AM NOT VALIDATING TYPES
        # I. AM. NOT. VALIDATING. TYPES.

        # both sides have actual values now, no references, just raw values (ints, strings)
        # column references have the format §table_name.column_name
        # pretty hacky solution but it'll do

        # if neither side is a column, just evaluate the condition

        left_is_col = False
        right_is_col = False

        if type(left_value) is str and left_value.startswith("§"):
            left_is_col = True
        if type(right_value) is str and right_value.startswith("§"):
            right_is_col = True

        # override offsets for audio search too lol
        if op == OperationType.DISTANCE and left_is_col and isinstance(right_value, str):
            bica_es_poder = left_value[1:].split(".")[1]
            Logger.log_debug(f"ENTERED DISTANCE SEARCH, {bica_es_poder}, {right_value}, {k}")
            return self.do_audio_knn(table_name, bica_es_poder, right_value, k)

        # override offsets for text search
        if op == OperationType.ATAT and left_is_col and isinstance(right_value, str):
            return self.do_text_search(table_name, right_value, k)

        # if neither side is a column, eval directly
        if not left_is_col and not right_is_col:

            def cmp():
                match op:
                    case OperationType.EQUAL:
                        return left_value == right_value
                    case OperationType.NOT_EQUAL:
                        return left_value != right_value
                    case OperationType.GREATER_THAN:
                        return left_value > right_value
                    case OperationType.LESS_THAN:
                        return left_value < right_value
                    case OperationType.GREATER__EQUAL:
                        return left_value >= right_value
                    case OperationType.LESS__EQUAL:
                        return left_value <= right_value
                    case OperationType.BETWEEN:
                        return right_value[0] <= left_value <= right_value[1]
                    case _:
                        raise ValueError(f"Unsupported operation {op}")

            return self.fetch_all_offsets(table_name) if cmp() else set()

        # if left is column use left as field and right as value
        if left_is_col:
            field = left_value[1:].split(".")[1]  # remove § and get column name
            value = right_value
        # if right is column use right as field and left as value
        elif right_is_col:
            field = right_value[1:].split(".")[1]  # remove the § and get the column name
            value = left_value
            # reverse toperator in case right is column
            op = {
                OperationType.GREATER_THAN: OperationType.LESS_THAN,
                OperationType.LESS_THAN: OperationType.GREATER_THAN,
                OperationType.GREATER__EQUAL: OperationType.LESS__EQUAL,
                OperationType.LESS__EQUAL: OperationType.GREATER__EQUAL,
            }.get(op, op)

        # mega big brain move
        priority_map: dict[OperationType, list[tuple]] = {
            OperationType.EQUAL: [
                (self.check_hash_idx, self.search_hash_idx),
                (self.check_btree_idx, self.search_btree_idx),
                (self.check_seq_idx, self.search_seq_idx),
                (self.check_rtree_idx, self.search_rtree_record),
            ],
            OperationType.GREATER__EQUAL: [
                (self.check_btree_idx, self.search_btree_idx_range),
                (self.check_seq_idx, self.search_seq_idx_range),
            ],
            OperationType.LESS__EQUAL: [
                (self.check_btree_idx, self.search_btree_idx_range),
                (self.check_seq_idx, self.search_seq_idx_range),
            ],
            OperationType.GREATER_THAN: [
                (self.check_btree_idx, self.search_btree_idx_range),
                (self.check_seq_idx, self.search_seq_idx_range),
            ],
            OperationType.LESS_THAN: [
                (self.check_btree_idx, self.search_btree_idx_range),
                (self.check_seq_idx, self.search_seq_idx_range),
            ],
        }

        # mucha gracia jesval
        for check, search in priority_map.get(op, []):
            if check(table_name, field):
                return search(table_name, field, value)

        # fallback sequential scan on heap
        def cmp(v):
            match op:
                case OperationType.EQUAL:
                    return v == value
                case OperationType.NOT_EQUAL:
                    return v != value
                case OperationType.GREATER_THAN:
                    return v > value
                case OperationType.LESS_THAN:
                    return v < value
                case OperationType.GREATER__EQUAL:
                    return v >= value
                case OperationType.LESS__EQUAL:
                    return v <= value
                case OperationType.BETWEEN:
                    return value[0] <= v <= value[1]
                case _:
                    raise ValueError(f"Unsupported operation {op} for field {field} in table {table_name}.")

        heap: HeapFile = DBManager.get_table_heap(table_name)
        all_pairs: List[Tuple[Union[int, float, str], int]] = heap.extract_index(field)
        return {off for v, off in all_pairs if cmp(v)}

    def records_projection(
        self,
        table_name: str,
        offsets: set[int],
        columns: list[str] | None,
        as_df: bool = False,
    ) -> list[list] | pd.DataFrame:
        heap: HeapFile = DBManager.get_table_heap(table_name)
        schema: list[tuple] = DBManager.get_table_schema(table_name)
        names = [name for name, _ in schema]
        if columns:
            for col in columns:
                if col not in names:
                    raise ValueError(f"Column '{col}' does not exist in table '{table_name}'.")
        else:
            columns = names
        positions: list[int] = [DBManager.get_column_position(table_name, col) for col in columns]
        results: list[list] = []
        for offset in offsets:
            record: Record = heap.fetch_record_by_offset(offset)
            results.append([record.values[pos] for pos in positions])
        return pd.DataFrame(results, columns=columns) if as_df else results

    def fetch_all_offsets(self, table_name: str) -> set[int]:
        DBManager.verify_table_exists(table_name)
        return HeapFile(DBManager.table_path(table_name)).get_all_offsets()

    def column_to_list(self, table_name: str, column_name: str) -> list:
        offsets = DBManager().fetch_all_offsets(table_name)
        pos = DBManager.get_column_position(table_name, column_name)
        heap = DBManager.get_table_heap(table_name)
        values = []
        for offset in offsets:
            record = heap.fetch_record_by_offset(offset)
            values.append(record.values[pos])
        return values

    def audio_spimi_exists(self, table_name: str, field_name: str) -> bool:
        return os.path.exists(os.path.join(self.tables_dir, f"{table_name}.{field_name}_norms.dat"))

    def do_audio_knn(self, table_name: str, column_name: str, query_text: str, k: int) -> set[int]:
        Logger.log_debug("ALL GOOD")
        if self.audio_spimi_exists(table_name, column_name):
            return knn_search_index(table_name, column_name, query_text, k)
        else:
            return knn_search(table_name, column_name, query_text, k)

    def do_text_search(self, table_name: str, query_text: str, k: int) -> set[int]:
        return search_text(table_name, query_text, k)
