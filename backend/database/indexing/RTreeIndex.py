import os
from rtree import index
import json
from .IndexRecord import IndexRecord
from . import utils

class RTreeIndex:
    def __init__(self, table_name: str, indexed_field: str):
        # Validate scheme and field
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
    def build_index(heap_filename: str, extract_index_fn, key_field: str):
        # Load schema
        schema = utils.load_schema(heap_filename)
        # Get key format
        key_format = utils.get_key_format_from_schema(schema, key_field)
        
        # Generate index filename
        base, _ = os.path.splitext(heap_filename)
        idx_filename = f"{base}.{key_field}.rtree.idx"

        # Create index using library
        props = index.Property()
        props.storage = index.RT_Disk
        idx = index.Index(idx_filename, properties = props)

        # Extract and validate entries
        entries = extract_index_fn(key_field)
        