import os
import glob
import time
from typing import List, Tuple, Optional, Union
from storage.HeapFile import HeapFile
from storage.Record import Record
from indexing.SequentialIndex import SequentialIndex
from indexing.ExtendibleHashIndex import ExtendibleHashIndex
from indexing.BPlusTreeIndex import BPlusTreeIndex, BPlusTreeIndexWrapper
from indexing.IndexRecord import IndexRecord
from indexing.RTreeIndex import RTreeIndex

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


    # Helper methods for managing tables and schemas
    @staticmethod
    def _table_path(table_name: str) -> str:
        """Devuelve la ruta absoluta (sin extensión) de la tabla."""
        return os.path.join(DBManager.tables_dir, table_name)
    
    @staticmethod
    def check_table_exists(table_name: str):
     return os.path.exists(DBManager._table_path(table_name) + ".dat")
    
    @staticmethod
    def get_table_schema(table_name: str):
        if not DBManager.check_table_exists(table_name):
            raise FileNotFoundError(f"Table {table_name} does not exist")
        schema_path = DBManager._table_path(table_name) + ".schema.json"
        return HeapFile._load_schema_from_file(schema_path)
    
    @staticmethod
    def create_table(table_name: str, schema: List[Tuple[str, str]],
                     primary_key: Optional[str] = None) -> None:
        HeapFile.build_file(DBManager._table_path(table_name), schema, primary_key)
        print(f"Tabla {table_name} creada con éxito.")

    # Index management methods

    # Index creation methods
    @staticmethod
    def create_seq_idx(table_name: str, field_name: str) -> None:
        path = DBManager._table_path(table_name)
        SequentialIndex.build_index(path, HeapFile(path).extract_index, field_name)
        print(f"Índice secuencial creado para {field_name} en la tabla {table_name}.")

    @staticmethod
    def create_hash_idx(table_name: str, field_name: str) -> None:
        path = DBManager._table_path(table_name)
        ExtendibleHashIndex.build_index(path, HeapFile(path).extract_index, field_name)
        print(f"Índice hash creado para {field_name} en la tabla {table_name}.")

    @staticmethod
    def create_btree_idx(table_name: str, field_name: str) -> None:
        path = DBManager._table_path(table_name)
        BPlusTreeIndex.build_index(path, HeapFile(path).extract_index, field_name)
        print(f"Índice B+Tree creado para {field_name} en la tabla {table_name}.")

    @staticmethod
    def create_rtree_idx(table_name: str, field_name: str) -> None:
        path = DBManager._table_path(table_name)
        RTreeIndex.build_index(path, HeapFile(path).extract_index, field_name)
        print(f"Índice R-Tree creado para {field_name} en la tabla {table_name}.")

    # Index verification methods
    @staticmethod
    def check_seq_idx(table_name: str, field: str) -> bool:
        table_path = DBManager._table_path(table_name)
        index_path = f"{table_path}.{field}.seq.idx"
        return os.path.exists(index_path)
    
    @staticmethod
    def check_hash_idx(table_name: str, field: str) -> bool:
        table_path = DBManager._table_path(table_name)
        index_paths = (f"{table_path}.{field}.btree.{ext}" for ext in ("idx", "db", "tree"))
        return all(os.path.exists(index_path) for index_path in index_paths)
    
    @staticmethod
    def check_btree_idx(table_name: str, field: str) -> bool:
        table_path = DBManager._table_path(table_name)
        index_path = f"{table_path}.{field}.btree.idx"
        return os.path.exists(index_path)
    
    @staticmethod
    def check_rtree_idx(table_name: str, field: str) -> bool:
        table_path = DBManager._table_path(table_name)
        index_paths = (f"{table_path}.{field}.rtree.{ext}" for ext in ("idx", "dat"))
        return all(os.path.exists(index_path) for index_path in index_paths)

    # Index deletion methods    
    @staticmethod
    def drop_seq_idx(table_name: str, field) -> None:
        table_path = DBManager._table_path(table_name)
        index_path = f"{table_path}.{field}.seq.idx"
        if not os.path.exists(index_path):
            raise FileNotFoundError(f"Índice secuencial para {field} en la tabla {table_name} no existe.")
        os.remove(index_path)
        print(f"Índice secuencial para {field} en la tabla {table_name} eliminado con éxito.")
    
    @staticmethod
    def drop_hash_idx(table_name: str, field) -> None:
        table_path = DBManager._table_path(table_name)
        index_paths = (f"{table_path}.{field}.btree.{ext}" for ext in ("idx", "db", "tree"))
        for index_path in index_paths:
            if not os.path.exists(index_path):
                raise FileNotFoundError(f"Índice Hash para {field} en la tabla {table_name} no existe.")
            os.remove(index_path)
        print(f"Índice hash para {field} en la tabla {table_name} eliminado con éxito.")

    @staticmethod
    def drop_btree_idx(table_name: str, field) -> None:
        table_path = DBManager._table_path(table_name)
        index_path = f"{table_path}.{field}.btree.idx"
        if not os.path.exists(index_path):
            raise FileNotFoundError(f"Índice B+Tree para {field} en la tabla {table_name} no existe.")
        os.remove(index_path)
        print(f"Índice B+Tree para {field} en la tabla {table_name} eliminado con éxito.")
    
    @staticmethod
    def drop_rtree_idx(table_name: str, field) -> None:
        table_path = DBManager._table_path(table_name)
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
        table_path = DBManager._table_path(table_name)
        fields = [name for name, _ in DBManager.get_table_schema(table_name)]
        for field in fields:
            DBManager.drop_all_indexes_field(table_name, field)