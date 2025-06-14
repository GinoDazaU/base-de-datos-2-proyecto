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

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(DBManager, cls).__new__(cls, *args, **kwargs)
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.tables_dir = os.path.join(self.base_dir, "tables")
        os.makedirs(self.tables_dir, exist_ok=True)
        self._initialized = True