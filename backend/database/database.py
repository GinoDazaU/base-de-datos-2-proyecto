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
    """Crea un HeapFile vacío y su esquema JSON.

    Args:
        table_name: nombre lógico.
        schema: [(campo, fmt)].
        primary_key: nombre del campo PK o None.
    """
    HeapFile.build_file(_table_path(table_name), schema, primary_key)


def create_isam_table(table_name: str,
                      schema: List[Tuple[str, str]],
                      key_field: str,
                      block_factor: int = 8) -> None:
    ISAM.build_isam(_table_path(table_name), schema, key_field, block_factor)

# ---------------------------------------------------------------------------
#  Inserción de registros ----------------------------------------------------
# ---------------------------------------------------------------------------

def _update_secondary_indexes(table_path: str,
                              record: Record,
                              offset: int) -> None:
    """Actualiza todos los índices *.idx* que existan para la tabla."""
    schema = record.schema
    for idx_file in glob.glob(f"{table_path}.*.*.idx"):
        parts = os.path.basename(idx_file).split('.')
        if len(parts) < 4:
            continue  # formato inesperado

        field_name, idx_type = parts[1], parts[2]
        field_type = next((fmt for name, fmt in schema if name == field_name), None)
        if field_type is None:
            continue  # campo ya no existe

        field_value = record.values[[n for n, _ in schema].index(field_name)]
        idx_rec = IndexRecord(field_type, field_value, offset)

        if idx_type == "seq":
            SequentialIndex(table_path, field_name).insert_record(idx_rec)
        elif idx_type == "hash":
            ExtendibleHashIndex(table_path, field_name).insert_record(idx_rec)
        elif idx_type == "btree":
            BPlusTreeIndex(table_path, field_name).insert_record(idx_rec)


def insert_record(table_name: str, record: Record) -> int:
    table_path = _table_path(table_name)
    heap = HeapFile(table_path)
    offset = heap.insert_record(record)  # puede lanzar ValueError si PK duplicada
    _update_secondary_indexes(table_path, record, offset)
    return offset

# ---------------------------------------------------------------------------
#  Impresión y depuración ----------------------------------------------------
# ---------------------------------------------------------------------------

def print_table(table_name: str) -> None:
    HeapFile(_table_path(table_name)).print_all()

# ---------------------------------------------------------------------------
#  Índice secuencial ---------------------------------------------------------
# ---------------------------------------------------------------------------

def create_seq_idx(table_name: str, field_name: str) -> None:
    table_path = _table_path(table_name)
    heap = HeapFile(table_path)
    SequentialIndex.build_index(table_path, heap.extract_index, field_name)


def search_seq_idx(table_name: str, field_name: str, field_value):
    table_path = _table_path(table_name)
    heap = HeapFile(table_path)
    seq_idx = SequentialIndex(table_path, field_name)
    for idx_rec in seq_idx.search_record(field_value):
        heap.fetch_record_by_offset(idx_rec.offset).print()


def print_all_seq_idx(table_name: str, field_name: str) -> None:
    SequentialIndex(_table_path(table_name), field_name).print_all()

# ---------------------------------------------------------------------------
#  Prueba rápida -------------------------------------------------------------
# ---------------------------------------------------------------------------

def test1():
    table_name = "Productos"
    schema = [
        ("id", "i"),
        ("nombre", "20s"),
        ("precio", "f"),
        ("cantidad", "i"),
    ]

    # Crear tabla con clave primaria "id"
    create_table(table_name, schema, primary_key="id")

    registros = [
        Record(schema, [5, "Galletas", 3.5, 10]),
        Record(schema, [2, "Chocolate", 5.2, 8]),
        Record(schema, [7, "Caramelos", 1.75, 25]),
        Record(schema, [1, "Cereal", 4.0, 12]),
        Record(schema, [9, "Yogurt", 2.8, 6]),
        Record(schema, [10, "Yogurt", 2.5, 3]),
        Record(schema, [4, "Pan", 1.5, 20]),
        Record(schema, [6, "Leche", 3.1, 15]),
    ]

    for r in registros:
        insert_record(table_name, r)

    print_table(table_name)

    # Índice secuencial sobre "nombre"
    create_seq_idx(table_name, "nombre")
    print_all_seq_idx(table_name, "nombre")

    # Índice secuencial sobre "precio"
    create_seq_idx(table_name, "precio")
    print_all_seq_idx(table_name, "precio")

    # Búsqueda con índice secuencial
    print("\nBuscando yogurt con índice secuencial:")
    search_seq_idx(table_name, "nombre", "Yogurt")

    # Intento de duplicar PK (debe fallar)
    try:
        insert_record(table_name, registros[4])  # id = 9 duplicado
    except ValueError as e:
        print("\nError (esperado por PK duplicada):", e)

    # El índice secuencial no cambia porque la inserción falló
    print_all_seq_idx(table_name, "nombre")

if __name__ == "__main__":
    test1()
