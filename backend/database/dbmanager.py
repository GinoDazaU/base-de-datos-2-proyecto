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