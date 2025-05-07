import os
import glob
from storage.HeapFile import HeapFile
from storage.Record import Record
from indexing.SequentialIndex import SequentialIndex
from indexing.ExtendibleHashIndex import ExtendibleHashIndex
from indexing.BPlusTreeIndex import BPlusTreeIndex
from indexing.IndexRecord import IndexRecord

base_dir = os.path.dirname(os.path.abspath(__file__))
tables_dir = os.path.join(base_dir, "tables")
os.makedirs(tables_dir, exist_ok=True)

def get_table_path(table_name):
    return os.path.join(tables_dir, table_name)

def create_table(table_name: str, schema: list[tuple[str:str]]):
    table_name = get_table_path(table_name)
    HeapFile.build_file(table_name, schema)

def insert_record(table_name: str, record: Record):
    table_path = get_table_path(table_name)
    heap = HeapFile(table_path)
    offset = heap.insert_record(record)
    schema = heap.schema
    
    for idx_file in glob.glob(f"{table_path}.*.*.idx"):
        parts = os.path.basename(idx_file).split('.')
        if len(parts) < 4:
            continue
            
        field_name, idx_type = parts[1], parts[2]
        field_type = next((f[1] for f in schema if f[0] == field_name), None)
        
        if field_type:
            field_value = record.values[schema.index((field_name, field_type))]
            index_record = IndexRecord(field_type, field_value, offset)
            
            if idx_type == "seq":
                SequentialIndex(table_path, field_name).insert_record(index_record)
            if idx_type == "hash":
                ExtendibleHashIndex(table_path, field_name).insert_record(index_record)
            if idx_file == "btree":
                pass

def print_table(table_name: str):
    table_name = get_table_path(table_name)
    heap = HeapFile(table_name)
    heap.print_all()

def create_seq_idx(table_name: str, field_name):
    table_name = get_table_path(table_name)
    heap = HeapFile(table_name)
    SequentialIndex.build_index(table_name, heap.extract_index, field_name)

def search_seq_idx(table_name: str, field_name, field_value):
    table_name = get_table_path(table_name)
    heap = HeapFile(table_name)
    seq_idx = SequentialIndex(table_name, field_name)
    matching_records = seq_idx.search_record(field_value)
    for idx_record in matching_records:
        record = heap.fetch_record_by_offset(idx_record.offset)
        record.print()

def print_all_seq_idx(table_name: str, field_name: str):
    table_name = get_table_path(table_name)
    seq_idx = SequentialIndex(table_name, field_name)
    seq_idx.print_all()

# para probar las funciones
def test():
    table_name = "test"
    schema = [("id", "i"), ("nombre", "20s"), ("precio", "f"), ("cantidad", "i")]

    create_table(table_name, schema)

    records = [
        Record(schema, [5, "Galletas", 3.5, 10]),
        Record(schema, [2, "Chocolate", 5.2, 8]),
        Record(schema, [7, "Caramelos", 1.75, 25]),
        Record(schema, [1, "Cereal", 4.0, 12]),
        Record(schema, [9, "Yogurt", 2.8, 6]),
        Record(schema, [10, "Yogurt", 2.5, 3]),
        Record(schema, [4, "Pan", 1.5, 20]),
        Record(schema, [6, "Leche", 3.1, 15]),
    ]

    for r in records:
        insert_record(table_name, r)

    print_table(table_name)

    create_seq_idx(table_name, "nombre")

    print_all_seq_idx(table_name, "nombre")

    create_seq_idx(table_name, "precio")

    print_all_seq_idx(table_name, "precio")

    print("\n Buscando yogurt:") # hay dos yogurt en el heapfile se debe mostrar ambos
    search_seq_idx(table_name, "nombre" , "Yogurt")

    insert_record(table_name, records[4])

    print_all_seq_idx(table_name, "nombre")
