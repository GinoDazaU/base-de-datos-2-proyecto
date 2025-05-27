# =============================================================================
# 📦 Módulos y configuraciones iniciales
# =============================================================================

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

# Ruta base para almacenamiento de tablas
base_dir = os.path.dirname(os.path.abspath(__file__))
tables_dir = os.path.join(base_dir, "tables")
os.makedirs(tables_dir, exist_ok=True)

# =============================================================================
# 📁 Utilidades de rutas
# =============================================================================

def _table_path(table_name: str) -> str:
    """Devuelve la ruta absoluta (sin extensión) de la tabla."""
    return os.path.join(tables_dir, table_name)

# =============================================================================
# 🧱 Creación de tablas
# =============================================================================

def create_table(table_name: str, schema: List[Tuple[str, str]], primary_key: str) -> None:
    HeapFile.build_file(_table_path(table_name), schema, primary_key)

def create_table_with_btree_pk(table_name: str, schema: List[Tuple[str, str]], primary_key: str,) -> None:
    create_table(table_name, schema, primary_key)
    create_btree_idx(table_name, primary_key)

def create_table_with_hash_pk(table_name: str, schema: List[Tuple[str, str]], primary_key: str) -> None:
    create_table(table_name, schema, primary_key)
    create_hash_idx(table_name, primary_key)

# =============================================================================
# 🧱 Eliminar de tablas
# =============================================================================

def drop_table(table_name: str) -> None:
    table_path = _table_path(table_name)
    if not os.path.exists(f"{table_path}.dat"):
        raise FileNotFoundError(f"La tabla '{table_name}' no existe.")
    
    # Eliminar el archivo principal de la tabla
    os.remove(f"{table_path}.dat")

    if not os.path.exists(f"{table_path}.schema.json"):
        raise FileNotFoundError(f"El archivo de esquema de la tabla '{table_name}' no existe.")

    os.remove(f"{table_path}.schema.json")

    # Eliminar todos los índices asociados
    drop_all_indexes(table_name)

# =============================================================================
# ✏️ Inserción y eliminación de registros
# =============================================================================

def insert_record(table_name: str, record: Record) -> int:
    table_path = _table_path(table_name)
    heap = HeapFile(table_path)
    offset = heap.insert_record(record)
    _update_secondary_indexes(table_path, record, offset)
    return offset

def insert_record_free(table_name: str, record: Record) -> int:
    """Esto es de testing (no usar en frontend)"""
    table_path = _table_path(table_name)
    heap = HeapFile(table_path)
    return heap.insert_record_free(record)

def insert_record_hash_pk(table_name: str, record: Record) -> int:
    table_path = _table_path(table_name)
    heap = HeapFile(table_path)

    if heap.primary_key is None:
        raise ValueError(f"La tabla '{table_name}' no tiene clave primaria.")

    pk_idx = [i for i, (n, _) in enumerate(record.schema) if n == heap.primary_key][0]
    pk_value = record.values[pk_idx]

    hidx = ExtendibleHashIndex(table_path, heap.primary_key)
    if hidx.search_record(pk_value):
        raise ValueError(f"PK duplicada detectada por índice hash: {pk_value}")

    offset = heap.insert_record_free(record)
    _update_secondary_indexes(table_path, record, offset)
    return offset

def insert_record_btree_pk(table_name: str, record: Record) -> int:
    table_path = _table_path(table_name)
    heap = HeapFile(table_path)

    if heap.primary_key is None:
        raise ValueError(f"La tabla '{table_name}' no tiene clave primaria.")

    pk_idx = [i for i, (n, _) in enumerate(record.schema) if n == heap.primary_key][0]
    pk_value = record.values[pk_idx]

    btree = BPlusTreeIndexWrapper(table_path, heap.primary_key)
    if btree.search(pk_value):
        raise ValueError(f"PK duplicada detectada por índice B+ Tree: {pk_value}")

    offset = heap.insert_record_free(record)

    _update_secondary_indexes(table_path, record, offset)
    return offset

def insert_record_rtree_pk(table_name: str, record: Record) -> int:
    table_path = _table_path(table_name)
    heap = HeapFile(table_path)

    if heap.primary_key is None:
        raise ValueError(f"La tabla '{table_name}' no tiene clave primaria.")
    
    pk_idx = [i for i, (n, _) in enumerate(record.schema) if n == heap.primary_key][0]
    pk_value = record.values[pk_idx]

    rtree = RTreeIndex(table_path, heap.primary_key)
    if rtree.search_record(pk_value):
        raise ValueError(f"PK duplicada detectada por índice R-Tree: {pk_value}")
    
    offset = heap.insert_record_free(record)

    _update_secondary_indexes(table_path, record, offset)
    return offset

def delete_record(table_name: str, pk_value):
    table_path = _table_path(table_name)
    heap = HeapFile(table_path)
    ok, offset, old_rec = heap.delete_by_pk(pk_value)
    if not ok:
        return False
    _remove_from_secondary_indexes(table_path, old_rec, offset)
    return True

# =============================================================================
# 🔍 Búsqueda de registros
# =============================================================================

def search_by_field(table_name: str, field_name: str, value):
    return HeapFile(_table_path(table_name)).search_by_field(field_name, value)

def search_seq_idx(table_name: str, field_name: str, field_value):
    table_path = _table_path(table_name)
    heap = HeapFile(table_path)
    seq_idx = SequentialIndex(table_path, field_name)
    return [heap.fetch_record_by_offset(r.offset) for r in seq_idx.search_record(field_value)]

def search_btree_idx(table_name: str, field_name: str, field_value):
    table_path = _table_path(table_name)
    heap = HeapFile(table_path)
    btree = BPlusTreeIndexWrapper(table_path, field_name)
    offsets = btree.search(field_value)
    return [heap.fetch_record_by_offset(off) for off in offsets] if offsets else []

def search_btree_idx_range(table_name: str, field_name: str, start_value, end_value):
    table_path = _table_path(table_name)
    heap = HeapFile(table_path)
    btree = BPlusTreeIndexWrapper(table_path, field_name)
    offsets = btree.range_search(start_value, end_value)
    return [heap.fetch_record_by_offset(off) for off in offsets] if offsets else []

def search_hash_idx(table_name: str, field_name: str, field_value):
    table_path = _table_path(table_name)
    heap = HeapFile(table_path)
    hidx = ExtendibleHashIndex(table_path, field_name)
    return [heap.fetch_record_by_offset(r.offset) for r in hidx.search_record(field_value)]

def search_seq_idx_range(table_name: str, field_name: str, start_value, end_value):
    table_path = _table_path(table_name)
    heap = HeapFile(table_path)
    idx = SequentialIndex(table_path, field_name)
    records = idx.search_range(start_value, end_value)
    return [heap.fetch_record_by_offset(rec.offset) for rec in records]

def search_rtree_record(table_name: str, field_name: str, point: Tuple[Union[int, float], ...]) -> List[Record]:
    table_path = _table_path(table_name)
    heap = HeapFile(table_path)
    rtree = RTreeIndex(table_path, field_name)
    records = rtree.search_record(point)
    return [heap.fetch_record_by_offset(rec.offset) for rec in records]

def search_rtree_bounds(table_name: str, field_name: str, lower_bound: Tuple[Union[int, float], ...], upper_bound: Tuple[Union[int, float], ...]) -> List[Record]:
    table_path = _table_path(table_name)
    heap = HeapFile(table_path)
    rtree = RTreeIndex(table_path, field_name)
    records = rtree.search_bounds(lower_bound, upper_bound)
    return [heap.fetch_record_by_offset(rec.offset) for rec in records]

def search_rtree_radius(table_name: str, field_name: str, point: Tuple[Union[int, float], ...], radius: float) -> List[Record]:
    table_path = _table_path(table_name)
    heap = HeapFile(table_path)
    rtree = RTreeIndex(table_path, field_name)
    records = rtree.search_radius(point, radius)
    return [heap.fetch_record_by_offset(rec.offset) for rec in records]

def search_rtree_knn(table_name: str, field_name: str, point: Tuple[Union[int, float], ...], k: int) -> List[Record]:
    table_path = _table_path(table_name)
    heap = HeapFile(table_path)
    rtree = RTreeIndex(table_path, field_name)
    records = rtree.search_knn(point, k)
    return [heap.fetch_record_by_offset(rec.offset) for rec in records]

# =============================================================================
# 🧠 Mantenimiento de índices secundarios
# =============================================================================

def _update_secondary_indexes(table_path: str, record: Record, offset: int) -> None:
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
        idx_rec = IndexRecord(field_type, value, offset)
        if idx_type == "seq":
            SequentialIndex(table_path, field_name).insert_record(idx_rec)
        elif idx_type == "hash":
            ExtendibleHashIndex(table_path, field_name).insert_record(idx_rec)
        elif idx_type == "btree":
            start = time.time()
            BPlusTreeIndexWrapper(table_path, field_name).insert_record(idx_rec)
            end = time.time()
            print(f"[DEBUG Tiempo B+Tree Insert] {field_name}: {end - start:.6f} s")
        elif idx_type == "rtree":
            RTreeIndex(table_path, field_name).insert_record(idx_rec)

def _remove_from_secondary_indexes(table_path: str, record: Optional[Record], offset: int) -> None:
    if record is None:
        return  # No hay registro para eliminar
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
        elif idx_type == "hash":
            ExtendibleHashIndex(table_path, field_name).delete_record(value, offset)
        elif idx_type == "btree":
            BPlusTreeIndexWrapper(table_path, field_name).delete_record(value, offset)
        elif idx_type == "rtree":
            RTreeIndex(table_path, field_name).delete_record(value, offset)

# =============================================================================
# 🛠️ Creación de índices secundarios
# =============================================================================

def create_seq_idx(table_name: str, field_name: str):
    path = _table_path(table_name)
    SequentialIndex.build_index(path, HeapFile(path).extract_index, field_name)

def create_btree_idx(table_name: str, field_name: str):
    path = _table_path(table_name)
    BPlusTreeIndex.build_index(path, HeapFile(path).extract_index, field_name)

def create_hash_idx(table_name: str, field_name: str):
    path = _table_path(table_name)
    ExtendibleHashIndex.build_index(path, HeapFile(path).extract_index, field_name)

def create_rtree_idx(table_name: str, field_name: str):
    path = _table_path(table_name)
    RTreeIndex.build_index(path, HeapFile(path).extract_index, field_name)

# =============================================================================
# 🛠️ Eliminación de índices secundarios
# =============================================================================

def drop_seq_idx(table_name: str, field_name: str) -> None:
    table_path = _table_path(table_name)
    idx_path = f"{table_path}.{field_name}.seq.idx"
    if not os.path.exists(idx_path):
        raise FileNotFoundError(f"Index file {idx_path} does not exist.")
    os.remove(idx_path)

def drop_btree_idx(table_name: str, field_name: str) -> None:
    table_path = _table_path(table_name)
    idx_path = f"{table_path}.{field_name}.btree.idx"
    if not os.path.exists(idx_path):
        raise FileNotFoundError(f"Index file {idx_path} does not exist.")
    os.remove(idx_path)

def drop_hash_idx(table_name: str, field_name: str) -> None:
    table_path = _table_path(table_name)
    idx_paths = (f"{table_path}.{field_name}.hash.{ext}" for ext in ("db", "idx", "tree"))
    for idx_path in idx_paths:
        if not os.path.exists(idx_path):
            raise FileNotFoundError(f"Index file {idx_path} does not exist.")
        os.remove(idx_path)

def drop_rtree_idx(table_name: str, field_name: str) -> None:
    table_path = _table_path(table_name)
    idx_paths = (f"{table_path}.{field_name}.rtree.{ext}" for ext in ("idx", "dat"))
    for idx_path in idx_paths:
        if not os.path.exists(idx_path):
            raise FileNotFoundError(f"Index file {idx_path} does not exist.")
        os.remove(idx_path)

def drop_all_indexes_for_field(table_name: str, field_name: str) -> None:
    if check_seq_idx(table_name, field_name):
        drop_seq_idx(table_name, field_name)
    if check_btree_idx(table_name, field_name):
        drop_btree_idx(table_name, field_name)
    if check_hash_idx(table_name, field_name):
        drop_hash_idx(table_name, field_name)
    if check_rtree_idx(table_name, field_name):
        drop_rtree_idx(table_name, field_name)

def drop_all_indexes(table_name: str) -> None:
    path = _table_path(table_name)
    heap = HeapFile(path)
    fields = [name for name, _ in heap.schema]
    for field in fields:
        drop_all_indexes_for_field(table_name, field)

# =============================================================================
# 🛠️ Verificación de índices secundarios
# =============================================================================

def check_seq_idx(table_name: str, field_name: str) -> bool:
    table_path = _table_path(table_name)
    idx_path = f"{table_path}.{field_name}.seq.idx"
    return os.path.exists(idx_path)

def check_btree_idx(table_name: str, field_name: str) -> bool:
    table_path = _table_path(table_name)
    idx_path = f"{table_path}.{field_name}.btree.idx"
    return os.path.exists(idx_path)

def check_hash_idx(table_name: str, field_name: str) -> bool:
    table_path = _table_path(table_name)
    idx_paths = (f"{table_path}.{field_name}.hash.{ext}" for ext in ("db", "idx", "tree"))
    return all(os.path.exists(idx_path) for idx_path in idx_paths)

def check_rtree_idx(table_name: str, field_name: str) -> bool:
    table_path = _table_path(table_name)
    idx_paths = (f"{table_path}.{field_name}.rtree.{ext}" for ext in ("idx", "dat"))
    return all(os.path.exists(idx_path) for idx_path in idx_paths)

# =============================================================================
# 🧾 Impresión de estructuras (depuración)
# =============================================================================

def print_table(table_name: str):
    HeapFile(_table_path(table_name)).print_all()

def print_seq_idx(table_name: str, field_name: str):
    SequentialIndex(_table_path(table_name), field_name).print_all()

def print_hash_idx(table_name: str, field_name: str):
    ExtendibleHashIndex(_table_path(table_name), field_name).print_all()

def print_btree_idx(table_name: str, field_name: str):
    path = _table_path(table_name)
    BPlusTreeIndexWrapper(path, field_name).tree.scan_all()

def print_rtree_idx(table_name: str, field_name: str):
    RTreeIndex(_table_path(table_name), field_name).print_all()