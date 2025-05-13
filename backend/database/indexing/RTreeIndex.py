import os
from rtree import index
from typing import Tuple, List

class RTreeIndex:
    def __init__(self, table_name: str, field_name: str):
        self.index_name = f"{table_name}.{field_name}.rtree"
        if not os.path.exists(self.index_name + ".idx"):
            raise FileNotFoundError(f"El índice {self.index_name} no existe. Crea el índice primero.")
        
        props = index.Property()
        props.storage = index.RT_Disk
        self.idx = index.Index(self.index_name, properties=props)