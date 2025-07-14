import os
import glob
import time
from typing import List, Tuple, Optional, Union
from storage.HeapFile import HeapFile
from storage.Record import Record
from indexing.SequentialIndex import SequentialIndex
from indexing.ExtendibleHashIndex import ExtendibleHashIndex
from indexing.BPlusTreeIndex import BPlusTreeIndex, BPlusTreeIndexWrapper
from indexing.IndexRecord import IndexRecord, re_string, re_tuple
from indexing.RTreeIndex import RTreeIndex
from column_types import IndexType, ColumnType
from statement import CreateColumnDefinition, ConstantExpression
from fancytypes.schema import SchemaType

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
        if self._initialized:
            return
        self._initialized = True

    # region Helper methods
    @staticmethod
    def table_path(table_name: str) -> str:
        """Devuelve la ruta absoluta (sin extensión) de la tabla."""
        return os.path.join(DBManager.tables_dir, table_name)
    
    @staticmethod
    def check_table_exists(table_name: str) -> bool:
     return os.path.exists(DBManager.table_path(table_name) + ".dat") and os.path.exists(DBManager.table_path(table_name) + ".schema.json")
    
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
        return HeapFile._load_schema_from_file(schema_path)
    
    @staticmethod
    def get_field_format(table_name: str, field_name: str) -> str:
        schema = DBManager.get_table_schema(table_name)
        for name, field_name in schema:
            if name == field_name:
                return field_name
        raise ValueError(f"Field {field_name} not found in table {table_name}")
    
    @staticmethod
    def get_field_type(table_name: str, field_name: str) -> ColumnType:
        format = DBManager.get_field_format(table_name, field_name)
        match format:
            case 'i': return ColumnType.INT
            case 'f': return ColumnType.FLOAT
            case '?': return ColumnType.BOOL
            case "2f": return ColumnType.POINT2D
            case "3f": return ColumnType.POINT3D
            case _ if re_string.fullmatch(format): return ColumnType.VARCHAR
            case _: raise ValueError(f"Unknown format '{format}' for field '{field_name}' in table '{table_name}'")

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
            case _:
                raise ValueError(f"Unsupported column type: {column_type}")

    # region Index creation
    @staticmethod
    def create_seq_idx(table_name: str, field_name: str) -> None:
        type = DBManager.get_field_type(table_name, field_name)
        if type not in (ColumnType.INT, ColumnType.FLOAT, ColumnType.VARCHAR):
            raise ValueError(f"Índice no soportado para el campo {field_name} de tipo {type} en la tabla {table_name}.")
        path = DBManager.table_path(table_name)
        SequentialIndex.build_index(path, HeapFile(path).extract_index, field_name)

    @staticmethod
    def create_hash_idx(table_name: str, field_name: str) -> None:
        type = DBManager.get_field_type(table_name, field_name)
        if type not in (ColumnType.INT, ColumnType.VARCHAR):
            raise ValueError(f"Índice hash no soportado para el campo {field_name} de tipo {type} en la tabla {table_name}.")
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
        print(f"Índice secuencial para {field} en la tabla {table_name} eliminado con éxito.")
    
    @staticmethod
    def drop_hash_idx(table_name: str, field) -> None:
        table_path = DBManager.table_path(table_name)
        index_paths = (f"{table_path}.{field}.btree.{ext}" for ext in ("idx", "db", "tree"))
        for index_path in index_paths:
            if not os.path.exists(index_path):
                raise FileNotFoundError(f"Índice Hash para {field} en la tabla {table_name} no existe.")
            os.remove(index_path)
        print(f"Índice hash para {field} en la tabla {table_name} eliminado con éxito.")

    @staticmethod
    def drop_btree_idx(table_name: str, field) -> None:
        table_path = DBManager.table_path(table_name)
        index_path = f"{table_path}.{field}.btree.idx"
        if not os.path.exists(index_path):
            raise FileNotFoundError(f"Índice B+Tree para {field} en la tabla {table_name} no existe.")
        os.remove(index_path)
        print(f"Índice B+Tree para {field} en la tabla {table_name} eliminado con éxito.")
    
    @staticmethod
    def drop_rtree_idx(table_name: str, field) -> None:
        table_path = DBManager.table_path(table_name)
        index_paths = (f"{table_path}.{field}.rtree.{ext}" for ext in ("idx", "dat"))
        for index_path in index_paths:
            if not os.path.exists(index_path):
                raise FileNotFoundError(f"Índice R-Tree para {field} en la tabla {table_name} no existe.")
            os.remove(index_path)
        print(f"Índice R-Tree para {field} en la tabla {table_name} eliminado con éxito.")

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
    def search_seq_idx(table_name: str, field_name: str, field_value):
        table_path = DBManager.table_path(table_name)
        heap = HeapFile(table_path)
        seq_idx = SequentialIndex(table_path, field_name)
        return [heap.fetch_record_by_offset(r.offset) for r in seq_idx.search_record(field_value)]
    
    @staticmethod
    def search_seq_idx_range(table_name: str, field_name: str, start_value, end_value):
        table_path = DBManager.table_path(table_name)
        heap = HeapFile(table_path)
        idx = SequentialIndex(table_path, field_name)
        records = idx.search_range(start_value, end_value)
        return [heap.fetch_record_by_offset(rec.offset) for rec in records]
    
    @staticmethod
    def search_hash_idx(table_name: str, field_name: str, field_value):
        table_path = DBManager.table_path(table_name)
        heap = HeapFile(table_path)
        hidx = ExtendibleHashIndex(table_path, field_name)
        return [heap.fetch_record_by_offset(r.offset) for r in hidx.search_record(field_value)]
    
    @staticmethod
    def search_btree_idx(table_name: str, field_name: str, field_value):
        table_path = DBManager.table_path(table_name)
        heap = HeapFile(table_path)
        btree = BPlusTreeIndexWrapper(table_path, field_name)
        offsets = btree.search(field_value)
        return [heap.fetch_record_by_offset(off) for off in offsets] if offsets else []
    
    @staticmethod
    def search_btree_idx_range(table_name: str, field_name: str, start_value, end_value):
        table_path = DBManager.table_path(table_name)
        heap = HeapFile(table_path)
        btree = BPlusTreeIndexWrapper(table_path, field_name)
        offsets = btree.range_search(start_value, end_value)
        return [heap.fetch_record_by_offset(off) for off in offsets] if offsets else []

    @staticmethod
    def search_rtree_record(
    table_name: str, field_name: str, point: Tuple[Union[int, float], ...]) -> List[Record]:
        table_path = DBManager.table_path(table_name)
        heap = HeapFile(table_path)
        rtree = RTreeIndex(table_path, field_name)
        records = rtree.search_record(point)
        return [heap.fetch_record_by_offset(rec.offset) for rec in records]
    
    @staticmethod
    def search_rtree_bounds(table_name: str, field_name: str, lower_bound: Tuple[Union[int, float], ...],
    upper_bound: Tuple[Union[int, float], ...]) -> List[Record]:
        table_path = DBManager.table_path(table_name)
        heap = HeapFile(table_path)
        rtree = RTreeIndex(table_path, field_name)
        records = rtree.search_bounds(lower_bound, upper_bound)
        return [heap.fetch_record_by_offset(rec.offset) for rec in records]
    
    @staticmethod
    def search_rtree_radius(table_name: str, field_name: str, point: Tuple[Union[int, float], ...],
    radius: float) -> List[Record]:
        table_path = DBManager.table_path(table_name)
        heap = HeapFile(table_path)
        rtree = RTreeIndex(table_path, field_name)
        records = rtree.search_radius(point, radius)
        return [heap.fetch_record_by_offset(rec.offset) for rec in records]
    
    @staticmethod
    def search_rtree_knn(table_name: str, field_name: str, point: Tuple[Union[int, float], ...],
    k: int) -> List[Record]:
        table_path = DBManager.table_path(table_name)
        heap = HeapFile(table_path)
        rtree = RTreeIndex(table_path, field_name)
        records = rtree.search_knn(point, k)
        return [heap.fetch_record_by_offset(rec.offset) for rec in records]

    # region Main methods
    @staticmethod
    def create_table_aux(table_name: str, schema: List[Tuple[str, str]],
                     primary_key: Optional[str] = None) -> None:
        HeapFile.build_file(DBManager.table_path(table_name), schema, primary_key)
        print(f"Tabla {table_name} creada con éxito.")

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
    
    # region Parser helper functions

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
            case _:
                raise ValueError(f"Unkown index type: {index_type}")

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
        schema: list[tuple[str, str]] = DBManager.get_table_schema(table_name)
        schema_dict: dict = dict(schema)
        for column, value in zip(columns, values):
            if column not in schema_dict:
                raise ValueError(f"Column '{column}' does not exist in table '{table_name}'.")
            column_type = DBManager.get_field_type(table_name, column)
            map: dict = {
                ColumnType.INT: int,
                ColumnType.FLOAT: float,
                ColumnType.BOOL: bool,
                ColumnType.POINT2D: tuple[float, float],
                ColumnType.POINT3D: tuple[float, float, float],
                ColumnType.VARCHAR: str
            }
            if not isinstance(value, map[column_type]):
                raise TypeError(f"Value for column '{column}' must be of type {column_type}, got {type(value)}.")
        DBManager.insert_record(table_name, Record(schema, values))

    def select(self, columns: list[str], table_name: str, conditions: Optional[List]) -> List[Record]:
        pass