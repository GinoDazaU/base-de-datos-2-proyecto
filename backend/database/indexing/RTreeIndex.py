import os
from rtree import index
import json
from typing import Union, List, Tuple
from .IndexRecord import IndexRecord, re_tuple
from . import utils

class RTreeIndex:
    def __init__(self, table_name: str, indexed_field: str):
        # Validate schema and field
        self.schema = utils.load_schema(table_name)
        if indexed_field not in [f["name"] for f in self.schema["fields"]]:
            raise ValueError(f"Campo {indexed_field} no existe en el schema de {table_name}")
    
        self.filename = f"{table_name}.{indexed_field}.rtree.idx"

        # Validate if index file exists
        if not os.path.exists(self.filename):
            raise FileNotFoundError(f"El índice RTree para {table_name} en el campo {indexed_field} no existe. Crea el índice primero.")
        
        self.key_format = utils.get_key_format_from_schema(self.schema, indexed_field)

        # Load index using library
        props = index.Property()
        props.storage = index.RT_Disk
        self.idx = index.Index(self.filename, properties = props)

    @staticmethod
    def build_index(heap_filename: str, extract_index_fn, key_field: str) -> bool:
        # Load schema
        schema = utils.load_schema(heap_filename)
        # Get key format
        key_format: str = utils.get_key_format_from_schema(schema, key_field)
        
        # Generate index filename
        base, _ = os.path.splitext(heap_filename)
        idx_filename = f"{base}.{key_field}.rtree.idx"

        # Extract and validate entries
        entries = extract_index_fn(key_field)
        valid_entries = [(RTreeIndex.normalize_bounds(k), o) for k, o in entries if RTreeIndex.validate_type(k, key_format)]
        
        # Create index using library
        props = index.Property()
        props.storage = index.RT_Disk
        idx = index.Index(idx_filename, properties = props)

        # Write registers
        for key, offset in valid_entries:
            if not isinstance(offset, int):
                raise ValueError(f"Offset inválido: {offset}")
            idx.insert(offset, key)

        idx.close()
        return True

    @staticmethod
    def validate_type(value: Tuple[Union[int, float], ...], format: str) -> bool:
        m = re_tuple.fullmatch(format)
        if not m:
            return False
        
        n, type_char = int(m.group(1)), m.group(2)
        if n not in (2, 3, 4, 6) or not isinstance(value, tuple) or len(value) != n:
            return False
        
        if type_char == 'i':
            return all(isinstance(x, int) for x in value)
        
        return  all(isinstance(x, float) for x in value)

    @staticmethod
    def normalize_bounds(value: Tuple[Union[int, float], ...]) -> tuple:
        if len(value) == 2:
            x, y = value
            return (x, y, x, y)
        if len(value) == 3:
            x, y, z = value
            return (x, y, z, x, y, z)
        else:
            return value
        
    def insert_record(self, record: IndexRecord):
        if self.key_format != record.format:
            raise TypeError(f"El registro tiene format {record.format}, se esperaba {self.key_format}")
        
        if not isinstance(record.key, tuple):
            raise TypeError(f"El campo del registro es de tipo {type(record.key)}, se esperaba una tupla numérica")

        if not isinstance(record.offset, int):
           raise TypeError(f"Offset inválido (debe ser int), se recibió {type(record.offset)}")
        
        bounds = RTreeIndex.normalize_bounds(record.key)
        self.idx.insert(record.offset, bounds)
    
    def search_range(self, point: Tuple[Union[int, float], ...], radius: float) -> List[IndexRecord]:
        return NotImplemented
    
    def search_knn(self, point: Tuple[Union[int, float], ...], k: int) -> List[IndexRecord]:
        return NotImplemented

    def delete_record(self, key, offset) -> bool:
        return NotImplemented