import os
import glob
from typing import List, Tuple, Optional

from storage.HeapFile import HeapFile
from storage.Isam import ISAM
from storage.Record import Record
from indexing.SequentialIndex import SequentialIndex
from indexing.ExtendibleHashIndex import ExtendibleHashIndex
from indexing.BPlusTreeIndex import BPlusTreeIndex
from indexing.IndexRecord import IndexRecord

# ---------------------------------------------------------------------------
#  Directorio de trabajo: todas las tablas viven en ./tables
# ---------------------------------------------------------------------------
base_dir = os.path.dirname(os.path.abspath(__file__))
tables_dir = os.path.join(base_dir, "tables")
os.makedirs(tables_dir, exist_ok=True)

# ---------------------------------------------------------------------------
#  Utilidades de rutas -------------------------------------------------------
# ---------------------------------------------------------------------------

def _table_path(table_name: str) -> str:
    """Devuelve la ruta absoluta (sin extensión) de la tabla."""
    return os.path.join(tables_dir, table_name)

# ---------------------------------------------------------------------------
#  Creación de tablas --------------------------------------------------------
# ---------------------------------------------------------------------------

def create_table(table_name: str,
                 schema: List[Tuple[str, str]],
                 primary_key: Optional[str] = None) -> None:
    """Crea un HeapFile vacío y su esquema JSON."""
    HeapFile.build_file(_table_path(table_name), schema, primary_key)


def create_isam_table(table_name: str,
                      schema: List[Tuple[str, str]],
                      key_field: str,
                      block_factor: int = 8) -> None:
    ISAM.build_isam(_table_path(table_name), schema, key_field, block_factor)

def create_btree_table(table_name: str,
                       schema: List[Tuple[str, str]],
                       key_field: str,
                       is_primary_key: bool = True,
                       order: int = 4) -> None:
    
    HeapFile.build_file(_table_path(table_name), schema, key_field if is_primary_key else None)

    table_path = _table_path(table_name)
    heap = HeapFile(table_path)
    BPlusTreeIndex.build_index(table_path, heap.extract_index, key_field, is_unique=is_primary_key, order=order)

# ---------------------------------------------------------------------------
#  Índices secundarios -------------------------------------------------------
# ---------------------------------------------------------------------------

def _update_secondary_indexes(table_path: str, record: Record, offset: int) -> None:
    """Añade (value, offset) en todos los índices secundarios."""
    schema = record.schema
    for idx_file in glob.glob(f"{table_path}.*.*.idx"):
        parts = os.path.basename(idx_file).split('.')
        if len(parts) < 4:
            continue  # formato inesperado

        field_name, idx_type = parts[1], parts[2]
        field_type = next((fmt for name, fmt in schema if name == field_name), None)
        if field_type is None:
            continue  # campo ya no existe

        value = record.values[[n for n, _ in schema].index(field_name)]
        idx_rec = IndexRecord(field_type, value, offset)

        if idx_type == "seq":
            SequentialIndex(table_path, field_name).insert_record(idx_rec)
        elif idx_type == "hash":
            ExtendibleHashIndex(table_path, field_name).insert_record(idx_rec)
        elif idx_type == "btree":
            BPlusTreeIndex(table_path, field_name).insert_record(idx_rec)


def _remove_from_secondary_indexes(table_path: str, record: Record, offset: int) -> None:
    """Elimina (value, offset) de todos los índices secundarios.

    *La implementación real debe llamar al método correspondiente de cada
    estructura de índice para borrar solo ese offset.*"""
    schema = record.schema
    for idx_file in glob.glob(f"{table_path}.*.*.idx"):
        parts = os.path.basename(idx_file).split('.')
        if len(parts) < 4:
            continue
        field_name, idx_type = parts[1], parts[2]
        field_type = next((fmt for name, fmt in schema if name == field_name), None)
        if field_type is None:
            continue
        value = record.values[[n for n, _ in schema].index(field_name)]

        if idx_type == "seq":
            # SequentialIndex(table_path, field_name).delete_record(value, offset)
            pass
        elif idx_type == "hash":
            # ExtendibleHashIndex(table_path, field_name).delete_record(value, offset)
            pass
        elif idx_type == "btree":
            # BPlusTreeIndex(table_path, field_name).delete_record(value, offset)
            pass

# ---------------------------------------------------------------------------
#  Operaciones de datos ------------------------------------------------------
# ---------------------------------------------------------------------------

def insert_record(table_name: str, record: Record) -> int:
    table_path = _table_path(table_name)
    heap = HeapFile(table_path)
    offset = heap.insert_record(record)
    _update_secondary_indexes(table_path, record, offset)
    return offset


def delete_record(table_name: str, pk_value):
    """Elimina por clave primaria y actualiza índices secundarios."""
    table_path = _table_path(table_name)
    heap = HeapFile(table_path)
    ok, offset, old_rec = heap.delete_by_pk(pk_value)
    if not ok:
        return False
    _remove_from_secondary_indexes(table_path, old_rec, offset)
    return True

# ---------------------------------------------------------------------------
#  Utilidades de depuración --------------------------------------------------
# ---------------------------------------------------------------------------

def print_table(table_name: str):
    HeapFile(_table_path(table_name)).print_all()

# ---------------------------------------------------------------------------
#  Índice secuencial (helpers) ----------------------------------------------
# ---------------------------------------------------------------------------

def create_seq_idx(table_name: str, field_name: str):
    table_path = _table_path(table_name)
    heap = HeapFile(table_path)
    SequentialIndex.build_index(table_path, heap.extract_index, field_name)


def search_seq_idx(table_name: str, field_name: str, field_value):
    table_path = _table_path(table_name)
    heap = HeapFile(table_path)
    seq_idx = SequentialIndex(table_path, field_name)
    for idx_rec in seq_idx.search_record(field_value):
        heap.fetch_record_by_offset(idx_rec.offset).print()

def create_btree_idx(table_name: str, field_name: str):
    table_path = _table_path(table_name)
    heap = HeapFile(table_path)
    BPlusTreeIndex.build_index(table_path, heap.extract_index, field_name)

def search_btree_idx(table_name: str, field_name: str, field_value):
    table_path = _table_path(table_name)
    heap = HeapFile(table_path)
    btree = BPlusTreeIndex(table_path, field_name)

    offsets = btree.search(field_value)
    if not offsets:
        print("No results found.")
        return

    for offset in offsets:
        heap.fetch_record_by_offset(offset).print()


def print_all_seq_idx(table_name: str, field_name: str):
    SequentialIndex(_table_path(table_name), field_name).print_all()

# ---------------------------------------------------------------------------
#  Prueba rápida -------------------------------------------------------------
# ---------------------------------------------------------------------------

def _demo():
    tbl = "Productos"
    schema = [("id", "i"), ("nombre", "20s"), ("precio", "f"), ("cantidad", "i")]
    create_table(tbl, schema, primary_key="id")

    r1 = Record(schema, [1, "Galletas", 3.5, 10])
    r2 = Record(schema, [2, "Chocolate", 5.0, 8])
    insert_record(tbl, r1)
    insert_record(tbl, r2)

    print("-- tabla tras inserciones —")
    print_table(tbl)

    delete_record(tbl, 1)
    delete_record(tbl, 2)
    print("-- tabla tras delete(pk=1) —")
    print_table(tbl)

if __name__ == "__main__":
    _demo()
