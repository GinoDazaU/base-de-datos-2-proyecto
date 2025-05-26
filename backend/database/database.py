import os
import glob
from typing import List, Tuple, Optional

from storage.HeapFile import HeapFile
from storage.Isam import ISAM
from storage.Record import Record
from indexing.SequentialIndex import SequentialIndex
from indexing.ExtendibleHashIndex import ExtendibleHashIndex
from indexing.BPlusTreeIndex import BPlusTreeIndex, BPlusTreeIndexWrapper
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
                       order: int = 4) -> None:
    
    HeapFile.build_file(_table_path(table_name), schema, key_field)

    table_path = _table_path(table_name)
    heap = HeapFile(table_path)
    BPlusTreeIndex.build_index(table_path, heap.extract_index, key_field, order=order)

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
            BPlusTreeIndexWrapper(table_path, field_name).insert_record(idx_rec)


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
            SequentialIndex(table_path, field_name).delete_record(value, offset)
            pass
        elif idx_type == "hash":
            ExtendibleHashIndex(table_path, field_name).delete_record(value, offset)
            pass
        elif idx_type == "btree":
            BPlusTreeIndexWrapper(table_path, field_name).delete_record(value, offset)
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

def search_by_field(table_name: str, field_name: str, value):
    table_path = _table_path(table_name)
    heap = HeapFile(table_path)
    results = heap.search_by_field(field_name, value)
    return results

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
    results = []
    for idx_rec in seq_idx.search_record(field_value):
        results.append(heap.fetch_record_by_offset(idx_rec.offset))
    return results

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

    results = []
    for offset in offsets:
        results.append(heap.fetch_record_by_offset(offset))
    return results


def print_seq_idx(table_name: str, field_name: str):
    SequentialIndex(_table_path(table_name), field_name).print_all()

# ---------------------------------------------------------------------------
#  Índice hash (helpers) -----------------------------------------------------
# ---------------------------------------------------------------------------

def create_hash_idx(table_name: str, field_name: str,) -> None:
    """
    Construye un índice hash extensible (bucket fb, profundidad máxima max_depth)
    para `field_name` usando los valores actuales del HeapFile.
    """
    table_path = _table_path(table_name)
    heap = HeapFile(table_path)
    ExtendibleHashIndex.build_index(table_path, heap.extract_index, field_name)

def search_hash_idx(table_name: str, field_name: str, field_value):
    """Imprime los registros cuyo campo == field_value usando el índice hash."""
    table_path = _table_path(table_name)
    heap = HeapFile(table_path)
    hidx = ExtendibleHashIndex(table_path, field_name)
    results = []
    for idx_rec in hidx.search_record(field_value):
        results.append(heap.fetch_record_by_offset(idx_rec.offset))
    return results

def print_hash_idx(table_name: str, field_name: str):
    ExtendibleHashIndex(_table_path(table_name), field_name).print_all()

def create_table_with_hash_pk(table_name: str,
                               schema: List[Tuple[str, str]],
                               primary_key: str) -> None:
    """Crea la tabla y un índice hash extensible sobre la clave primaria."""
    create_table(table_name, schema, primary_key)
    create_hash_idx(table_name, primary_key)

def insert_record_hash_pk(table_name: str, record: Record) -> int:
    """
    Inserta un registro verificando unicidad de PK usando el índice hash,
    y si no existe, lo inserta sin validación usando insert_record_free.
    """
    table_path = _table_path(table_name)
    heap = HeapFile(table_path)

    if heap.primary_key is None:
        raise ValueError(f"La tabla '{table_name}' no tiene clave primaria.")

    pk_idx = [i for i, (n, _) in enumerate(record.schema) if n == heap.primary_key][0]
    pk_value = record.values[pk_idx]

    # buscar en índice hash
    hidx = ExtendibleHashIndex(table_path, heap.primary_key)
    if hidx.search_record(pk_value):
        raise ValueError(f"PK duplicada detectada por índice hash: {pk_value}")

    # insertar sin validación
    offset = heap.insert_record_free(record)

    # actualizar índices
    _update_secondary_indexes(table_path, record, offset)
    return offset
