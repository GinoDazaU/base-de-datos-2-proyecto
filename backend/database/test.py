import os
from storage.HeapFile import HeapFile
from indexing.SequentialIndex import SequentialIndex
from storage.Record import Record

base_dir = os.path.dirname(os.path.abspath(__file__))
tables_dir = os.path.join(base_dir, "tables")
os.makedirs(tables_dir, exist_ok=True)

def _get_table_path(table_name):
    return os.path.join(tables_dir, table_name)

def create_table(table_name: str, schema: list[tuple[str:str]]):
    table_name = _get_table_path(table_name)
    HeapFile.build_file(table_name, schema)

def create_seq_index(table_name: str, field_name):
    table_name = _get_table_path(table_name)
    heap = HeapFile(table_name)
    SequentialIndex.build_index(table_name, heap.extract_index, field_name)

def insert_record(table_name: str, record: Record):
    table_name = _get_table_path(table_name)
    heap = HeapFile(table_name)
    heap.insert_record(record)

def print_all_seq_idx(table_name: str, field_name: str):
    table_name = _get_table_path(table_name)
    seq_idx = SequentialIndex(table_name, field_name)
    seq_idx.print_all()

def main():
    table_name = "test"
    schema = [("id", "i"), ("nombre", "20s"), ("precio", "f"), ("cantidad", "i")]

    create_table(table_name, schema)

    records = [
        Record(schema, [5, "Galletas", 3.5, 10]),
        Record(schema, [2, "Chocolate", 5.2, 8]),
        Record(schema, [7, "Caramelos", 1.75, 25]),
        Record(schema, [1, "Cereal", 4.0, 12]),
        Record(schema, [9, "Yogurt", 2.8, 6]),
        Record(schema, [4, "Pan", 1.5, 20]),
        Record(schema, [6, "Leche", 3.1, 15]),
    ]

    for r in records:
        insert_record(table_name, r)

    create_seq_index(table_name, "nombre")

    print_all_seq_idx(table_name, "nombre")

    create_seq_index(table_name, "precio")

    print_all_seq_idx(table_name, "precio")

main()
