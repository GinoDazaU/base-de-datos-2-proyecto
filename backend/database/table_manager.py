import os
import glob
from pathlib import Path
from .storage.HeapFile import HeapFile
from .indexing.SequentialIndex import SequentialIndex
from .indexing.ExtendibleHashIndex import ExtendibleHashIndex
from .storage.Record import Record
from .indexing import IndexRecord

# Configuración simple y directa
TABLES_DIR = Path(__file__).parent / 'tables'
TABLES_DIR.mkdir(exist_ok=True)

def get_table_path(table_name: str) -> str:
    return str(TABLES_DIR / table_name)

def create_table(table_name: str, schema: list[tuple[str, str]]):
    HeapFile.build_file(get_table_path(table_name), schema)

def create_index(table_name: str, idx_type: str, field_name: str):
    """Crea cualquier tipo de índice en 3 líneas"""
    table_path = get_table_path(table_name)
    heap = HeapFile(table_path)
    
    if idx_type == "seq":
        SequentialIndex.build_index(table_path, heap.extract_index, field_name)
    elif idx_type == "hash":
        ExtendibleHashIndex.build_index(table_path, heap.extract_index, field_name)

class TableManager:
    def __init__(self, table_name: str):
        self.table_path = get_table_path(table_name)
        self.heapfile = HeapFile(self.table_path)
    
    def insert_record(self, record: Record):
        """Inserta y actualiza TODOS los índices automáticamente"""
        offset = self.heapfile.insert_record(record)
        
        # Actualiza cada índice encontrado
        for idx_file in glob.glob(f"{self.table_path}.*.*.idx"):
            parts = Path(idx_file).stem.split('.')
            if len(parts) == 3:  # tabla.campo.tipo
                field_name, idx_type = parts[1], parts[2]
                field_value = getattr(record, field_name)
                
                if idx_type == "seq":
                    idx = SequentialIndex(self.table_path, field_name)
                    idx.insert_record(IndexRecord(idx.key_format, field_value, offset))
                elif idx_type == "hash":
                    idx = ExtendibleHashIndex(self.table_path, field_name)
                    idx.insert_record(IndexRecord(idx.key_format, field_value, offset))
        
        return offset
    
    def get_schema(self):
        """Devuelve el schema sin complicaciones"""
        return self.heapfile.schema