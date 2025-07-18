# =============================================================================
# 📦 Módulos y configuraciones iniciales
# =============================================================================

import os
import glob
import time
import math
import json

from typing import List, Tuple, Optional, Union
from collections import Counter, defaultdict

from storage.HeapFile import HeapFile
from storage.Record import Record
from storage.Sound import Sound
from storage.HistogramFile import HistogramFile
from indexing.SequentialIndex import SequentialIndex
from indexing.ExtendibleHashIndex import ExtendibleHashIndex
from indexing.BPlusTreeIndex import BPlusTreeIndex, BPlusTreeIndexWrapper
from indexing.IndexRecord import IndexRecord
from indexing.RTreeIndex import RTreeIndex
from indexing.Spimi import SPIMIIndexer
from indexing.utils_spimi import preprocess
import pickle
from logger import Logger

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
# 📁 Utilidades para el parser
# =============================================================================


def check_table_exists(table_name: str):
    return os.path.exists(_table_path(table_name) + ".dat")


def get_table_schema(table_name: str):
    if not check_table_exists(table_name):
        raise Exception(f"Table {table_name} does not exist")
    table_path = _table_path(table_name)
    heap = HeapFile(table_path)  # TODO: load schema from file instead of creating heapfile
    return heap.schema


# =============================================================================
# 🧱 Creación de tablas
# =============================================================================


def create_table(table_name: str, schema: List[Tuple[str, str]], primary_key: str) -> None:
    for field_name, field_type in schema:
        if field_type.upper() == "SOUND":
            HistogramFile.build_file(_table_path(table_name), field_name)
    HeapFile.build_file(_table_path(table_name), schema, primary_key)

def create_table_with_btree_pk(
    table_name: str,
    schema: List[Tuple[str, str]],
    primary_key: str,
) -> None:
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

    # Eliminar archivos de texto asociados si hay campos de tipo TEXT
    try:
        schema = get_table_schema(table_name)
        for field_name, field_type in schema:
            if field_type.lower() == "text":
                txt_path = f"{table_path}.{field_name}.text"
                if os.path.exists(txt_path):
                    os.remove(txt_path)
    except Exception:
        # Si no existe la tabla o no se puede cargar el esquema, dejamos que
        # el flujo siga para lanzar el error correspondiente más abajo
        pass

    # Eliminar todos los índices asociados
    drop_all_indexes(table_name)

    # Eliminar el archivo principal de la tabla
    dat_path = f"{table_path}.dat"
    if not os.path.exists(dat_path):
        raise FileNotFoundError(f"La tabla '{table_name}' no existe.")
    os.remove(dat_path)

    # Eliminar el archivo principal de la tabla
    os.remove(f"{table_path}.dat")

    if not os.path.exists(f"{table_path}.schema.json"):
        raise FileNotFoundError(f"El archivo de esquema de la tabla '{table_name}' no existe.")

    os.remove(f"{table_path}.schema.json")

    print(f"Tabla '{table_name}' eliminada correctamente.")


# =============================================================================
# ✏️ Inserción y eliminación de registros
# =============================================================================


def insert_record(table_name: str, record: Record) -> int:
    table_path = _table_path(table_name)
    heap = HeapFile(table_path)

    values = list(record.values)
    for i, (field_name, field_type) in enumerate(record.schema):
        if field_type.upper() == "SOUND":
            sound_path = values[i]
            if isinstance(sound_path, str):
                sound_file = Sound(_table_path(table_name), field_name)
                sound_offset = sound_file.insert(sound_path)
                values[i] = (sound_offset, -1)  # -1 for histogram offset
    record.values = list(values)

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


def search_by_field(table_name: str, field_name: str, value, crude_data=False) -> List[Record]:
    return HeapFile(_table_path(table_name)).search_by_field(field_name, value, crude_data)


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


def search_rtree_bounds(
    table_name: str,
    field_name: str,
    lower_bound: Tuple[Union[int, float], ...],
    upper_bound: Tuple[Union[int, float], ...],
) -> List[Record]:
    table_path = _table_path(table_name)
    heap = HeapFile(table_path)
    rtree = RTreeIndex(table_path, field_name)
    records = rtree.search_bounds(lower_bound, upper_bound)
    return [heap.fetch_record_by_offset(rec.offset) for rec in records]


def search_rtree_radius(
    table_name: str,
    field_name: str,
    point: Tuple[Union[int, float], ...],
    radius: float,
) -> List[Record]:
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
        parts = os.path.basename(idx_file).split(".")
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
        elif idx_type == "rtree":
            RTreeIndex(table_path, field_name).insert_record(idx_rec)


def _remove_from_secondary_indexes(table_path: str, record: Optional[Record], offset: int) -> None:
    if record is None:
        return  # No hay registro para eliminar
    schema = record.schema
    for idx_file in glob.glob(f"{table_path}.*.*.idx"):
        parts = os.path.basename(idx_file).split(".")
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


# TODO: allow for index_name
def create_seq_idx(table_name: str, field_name: str):
    path = _table_path(table_name)
    SequentialIndex.build_index(path, HeapFile(path).extract_index, field_name)
    print(f"Índice secuencial creado para '{field_name}' en la tabla '{table_name}'.")


def create_btree_idx(table_name: str, field_name: str):
    path = _table_path(table_name)
    BPlusTreeIndex.build_index(path, HeapFile(path).extract_index, field_name)
    print(f"Índice B+ Tree creado para '{field_name}' en la tabla '{table_name}'.")


def create_hash_idx(table_name: str, field_name: str):
    path = _table_path(table_name)
    ExtendibleHashIndex.build_index(path, HeapFile(path).extract_index, field_name)
    print(f"Índice Extendible Hash creado para '{field_name}' en la tabla '{table_name}'.")


def create_rtree_idx(table_name: str, field_name: str):
    path = _table_path(table_name)
    RTreeIndex.build_index(path, HeapFile(path).extract_index, field_name)
    print(f"Índice R-Tree creado para '{field_name}' en la tabla '{table_name}'.")


# =============================================================================
# 🛠️ Eliminación de índices secundarios
# =============================================================================


def drop_seq_idx(table_name: str, field_name: str) -> None:
    table_path = _table_path(table_name)
    idx_path = f"{table_path}.{field_name}.seq.idx"
    if not os.path.exists(idx_path):
        raise FileNotFoundError(f"Index file {idx_path} does not exist.")
    os.remove(idx_path)
    print(f"Índice secuencial para '{field_name}' en la tabla '{table_name}' eliminado.")


def drop_btree_idx(table_name: str, field_name: str) -> None:
    table_path = _table_path(table_name)
    idx_path = f"{table_path}.{field_name}.btree.idx"
    if not os.path.exists(idx_path):
        raise FileNotFoundError(f"Index file {idx_path} does not exist.")
    os.remove(idx_path)
    print(f"Índice B+ Tree para '{field_name}' en la tabla '{table_name}' eliminado.")


def drop_hash_idx(table_name: str, field_name: str) -> None:
    table_path = _table_path(table_name)
    idx_paths = (f"{table_path}.{field_name}.hash.{ext}" for ext in ("db", "idx", "tree"))
    for idx_path in idx_paths:
        if not os.path.exists(idx_path):
            raise FileNotFoundError(f"Index file {idx_path} does not exist.")
        os.remove(idx_path)
    print(f"Índice Extendible Hash para '{field_name}' en la tabla '{table_name}' eliminado.")


def drop_rtree_idx(table_name: str, field_name: str) -> None:
    table_path = _table_path(table_name)
    idx_paths = (f"{table_path}.{field_name}.rtree.{ext}" for ext in ("idx", "dat"))
    for idx_path in idx_paths:
        if not os.path.exists(idx_path):
            raise FileNotFoundError(f"Index file {idx_path} does not exist.")
        os.remove(idx_path)
    print(f"Índice R-Tree para '{field_name}' en la tabla '{table_name}' eliminado.")

def drop_inverted_idx(table_name: str, field_name: str) -> None:
    # Eliminar todos los archivos cuyo nombre empiece por "inverted_index"
    pattern = os.path.join(tables_dir, "inverted_index*")
    files = glob.glob(pattern)
    if not files:
        raise FileNotFoundError("No se encontró ningún archivo de índice invertido para eliminar.")
    for fpath in files:
        os.remove(fpath)

def drop_all_indexes_for_field(table_name: str, field_name: str) -> None:
    if check_seq_idx(table_name, field_name):
        drop_seq_idx(table_name, field_name)
    if check_btree_idx(table_name, field_name):
        drop_btree_idx(table_name, field_name)
    if check_hash_idx(table_name, field_name):
        drop_hash_idx(table_name, field_name)
    if check_rtree_idx(table_name, field_name):
        drop_rtree_idx(table_name, field_name)
    if check_inverted_idx(table_name, field_name):
        drop_inverted_idx(table_name, field_name)

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

def check_inverted_idx(table_name: str, field_name: str) -> bool:
    return bool(glob.glob(f"{_table_path('inverted_index')}*"))

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


def build_spimi_index(table_name: str) -> None:
    """
    Construye el índice invertido SPIMI para los campos de tipo 'text' de la tabla.
    """
    indexer = SPIMIIndexer()
    indexer.build_index(_table_path(table_name))


def build_acoustic_index(table_name: str, field_name: str) -> None:
    """
    Construye el índice invertido para un campo de tipo 'SOUND'.
    """
    from indexing.SpimiAudio import SpimiAudioIndexer

    indexer = SpimiAudioIndexer(_table_path, field_name, index_table_name=f"{table_name}.{field_name}.idx")
    indexer.build_index(table_name)


def build_acoustic_model(table_name: str, field_name: str, num_clusters: int):
    """
    Construye un modelo acústico (codebook e histogramas) para un campo de audio.

    Args:
        table_name (str): Nombre de la tabla.
        field_name (str): Nombre del campo de tipo SOUND.
        num_clusters (int): Número de clusters para K-Means.
    """
    heap_file = HeapFile(_table_path(table_name))

    # 1. Construir el codebook
    from multimedia.codebook import build_codebook
    build_codebook(heap_file, field_name, num_clusters)
    # 2. Cargar el codebook
    from multimedia.histogram import load_codebook

    codebook = load_codebook(heap_file.table_name, field_name)
    if codebook is None:
        return

    # 3. Generar y almacenar histogramas
    from multimedia.histogram import build_histogram

    sound_handler = Sound(_table_path(table_name), field_name)
    histogram_handler = HistogramFile(_table_path(table_name), field_name)

    for record in heap_file.get_all_records():
        sound_offset, _ = record.values[heap_file.schema.index((field_name, "sound"))]
        audio_path = sound_handler.read(sound_offset)

        if audio_path is None:
            continue

        histogram = build_histogram(audio_path, codebook)
        if histogram is not None:
            # Convertir el histograma a una lista de tuplas (ID, COUNT)
            histogram_tuples = [(i, int(count)) for i, count in enumerate(histogram) if count > 0]

            # Insertar el histograma y obtener el offset
            histogram_offset = histogram_handler.insert(histogram_tuples)

            # Actualizar el registro en el heap file con el offset del histograma
            record.values = list(record.values)
            #Logger.log_spimi(record.values)

            record.values[heap_file.schema.index((field_name, "sound"))] = (
                sound_offset,
                histogram_offset,
            )
            #sLogger.log_spimi(record.values)

            heap_file.update_record(record)


def knn_search(table_name: str, field_name: str, query_audio_path: str, k: int) -> set[int]:
    """
    Realiza una búsqueda k-NN en un campo de audio.
    """
    Logger.log_debug("Starting sequential audio KNN")
    from multimedia.knn import knn_sequential_search

    heap_file = HeapFile(_table_path(table_name))
    return knn_sequential_search(query_audio_path, heap_file, field_name, k)


def knn_search_index(table_name: str, field_name: str, query_audio_path: str, k: int) -> set[int]:
    """
    Realiza una búsqueda k-NN en un campo de audio utilizando el índice invertido.
    """
    Logger.spimi_enabled=False

    Logger.log_debug("Starting indexed audio KNN")
    from multimedia.histogram import build_histogram, load_codebook
    from multimedia.knn import cosine_similarity, tf_idf
    import numpy as np

    # 1. Cargar codebook y construir histograma de consulta
    codebook = load_codebook(_table_path(table_name), field_name)
    if codebook is None:
        return []

    query_histogram = build_histogram(query_audio_path, codebook)
    if query_histogram is None:
        return []

    N = HeapFile(_table_path(table_name)).heap_size
    query_tfidf = np.zeros(len(codebook["centroids"]))
    for i, count in enumerate(query_histogram):
        if count > 0:
            query_tfidf[i] = tf_idf(count, codebook["doc_freq"][i], N)
    Logger.log_spimi(query_tfidf)
    # 2. Inicializar estructuras para el cálculo
    doc_scores = defaultdict(float)
    doc_norms = {}
    relevant_docs = set()

    # 3. Buscar términos en el índice acústico
    acoustic_index = HeapFile(_table_path(f"{table_name}.{field_name}.idx"))
    hash_idx = ExtendibleHashIndex(_table_path(f"{table_name}.{field_name}.idx"), "term")
    #acoustic_index.print_all()
    for term_id, tfidf_query in enumerate(query_tfidf):
        if tfidf_query > 0:
            index_records = hash_idx.search_record(term_id)
            if not index_records:
                continue
            #record = acoustic_index.fetch_record_by_offset(index_records[0].offset)
            record = acoustic_index.search_by_field("term", term_id)
            record=record[0]
            postings = json.loads(record.values[1])

            Logger.log_spimi(f"termid: {term_id} postngs")
            Logger.log_spimi(postings)


            for doc_id, tfidf_doc in postings:
                if doc_id==1:
                    Logger.log_spimi(f"termid: {term_id} {tfidf_query} {tfidf_doc}")

                doc_scores[doc_id] += tfidf_query * tfidf_doc
                relevant_docs.add(doc_id)

                if doc_id not in doc_norms:
                    norms_table = HeapFile(_table_path(f"{table_name}.{field_name}.idx_norms"))
                    hash_idx_norms = ExtendibleHashIndex(_table_path(f"{table_name}.{field_name}.idx_norms"), "doc_id")
                    norm_records = hash_idx_norms.search_record(doc_id)
                    if norm_records:
                        record = norms_table.fetch_record_by_offset(norm_records[0].offset)
                        doc_norms[doc_id] = record.values[1]
    Logger.log_spimi(relevant_docs)

    # 4. Calcular similitud coseno para documentos relevantes
    query_norm = np.linalg.norm(query_tfidf)
    scored_docs = []
    Logger.log_spimi("Norm docs")

    for doc_id in relevant_docs:
        doc_norm = doc_norms.get(doc_id, doc_id)
        if doc_id==1:
            Logger.log_spimi(f"{doc_id} {doc_norm}")

        similarity = doc_scores[doc_id] / (query_norm * doc_norm)
        scored_docs.append((doc_id, similarity))

    # 5. Obtener top-k documentos
    scored_docs.sort(key=lambda x: x[1], reverse=True)
    top_k = scored_docs[:k]

    # 6. Recuperar registros completos
    results = []
    source_table = HeapFile(_table_path(table_name))

    for doc_id, score in top_k:
        matching_recs = source_table.search_offsets_by_field("id", doc_id)
        if matching_recs:
            results.append((matching_recs[0], score))
    """
    # 7. Asignar similitud 0 a los documentos no encontrados
    all_doc_ids = {rec.values[0] for rec in source_table.get_all_records()}
    found_doc_ids = {res[0] for res in results}
    missing_doc_ids = all_doc_ids - found_doc_ids

    for doc_id in missing_doc_ids:
        matching_recs = source_table.search_offsets_by_field("id", doc_id)
        if matching_recs:
            results.append((matching_recs[0], 0.0))
    """

    results.sort(key=lambda x: x[1], reverse=True)

    offsets = set()
    similarity_scores = {}
    for offset, sim in results:
        offsets.add(offset)
        similarity_scores[offset] = sim
    Logger.debug_enabled=True
    Logger.log_debug(f"Audio indexed KNN obtained offsets: {offsets}")
    Logger.log_debug(f"Audio indexed KNN results: {similarity_scores}")

    return offsets


def search_text(table_name: str, query: str, k: int = 5) -> set[int]:
    """
    Búsqueda textual eficiente usando similitud coseno con TF-IDF
    - Precarga solo las normas necesarias
    - Optimiza el cálculo de similitud
    - Maneja correctamente tu estructura IndexRecord
    """
    # 1. Preprocesamiento de la consulta
    query_terms = preprocess(query)
    if not query_terms:
        return []

    # 2. Cargar frecuencias de términos en la consulta
    query_term_freq = defaultdict(int)
    for term in query_terms:
        query_term_freq[term] += 1
    unique_query_terms = list(query_term_freq.keys())

    # 3. Inicializar estructuras para el cálculo
    query_vector = {}
    doc_scores = defaultdict(float)
    doc_norms = {}
    relevant_docs = set()

    # 4. Buscar términos en índice invertido
    inverted_index = HeapFile(_table_path("inverted_index"))
    hash_idx = ExtendibleHashIndex(_table_path("inverted_index"), "term")

    for term in unique_query_terms:
        # 4.1 Buscar término usando índice hash
        index_records = hash_idx.search_record(term)
        if not index_records:
            continue

        # 4.2 Obtener el registro completo
        record = inverted_index.fetch_record_by_offset(index_records[0].offset)
        postings = json.loads(record.values[1])  # values[1] = postings JSON

        # 4.3 Calcular IDF para el término
        df_t = len(postings)
        idf = math.log(inverted_index.heap_size / df_t) if df_t else 0

        # 4.4 Peso del término en la consulta (TF normalizado * IDF)
        query_tf = query_term_freq[term] / len(query_terms)
        query_vector[term] = query_tf * idf

        # 4.5 Procesar postings del término
        for doc_id, tfidf in postings:
            doc_scores[doc_id] += query_vector[term] * tfidf
            relevant_docs.add(doc_id)

            # Almacenar norma si no está cargada
            if doc_id not in doc_norms:
                # Buscar norma para este doc (implementación optimizada)
                norms_table = HeapFile(_table_path("inverted_index_norms"))
                norm_records = norms_table.search_by_field("doc_id", doc_id)
                if norm_records:
                    doc_norms[doc_id] = norm_records[0].values[1]  # values[1] = norm

    # 5. Calcular similitud coseno para documentos relevantes
    query_norm = math.sqrt(sum(tfidf**2 for tfidf in query_vector.values()))
    scored_docs = []

    for doc_id in relevant_docs:
        doc_norm = doc_norms.get(doc_id, 1e-10)  # Evitar división por cero
        similarity = doc_scores[doc_id] / (query_norm * doc_norm)
        scored_docs.append((doc_id, similarity))

    # 6. Obtener top-k documentos
    scored_docs.sort(key=lambda x: x[1], reverse=True)
    top_k = scored_docs[:k]

    # 7. Recuperar registros completos
    heap_file = HeapFile(_table_path(table_name))
    offsets: set[int] = {heap_file.search_offsets_by_field("id", doc_id)[0] for doc_id, _ in top_k}
    Logger.log_debug(f"Obtained offsets: {offsets}")

    return offsets
