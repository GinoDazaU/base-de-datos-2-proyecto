from __future__ import annotations
"""
extendible_hash_index.py ― Índice Hash Extensible persistente
------------------------------------------------------------
Diseño base compatible con la arquitectura del proyecto:
*   Un **directorio** lógico se guarda como un árbol binario (ramas 0/1) serializado
    mediante *pickle* en `<table>.<field>.hash.tree`.
*   Los **buckets** (incluidos los de overflow) se almacenan de forma contigua
    en `<table>.<field>.hash.idx` tras un encabezado global.
*   Profundidad global máx. (`MAX_DEPTH`) configurable (por defecto 16 bits ⇒
    65 536 entradas potenciales en el directorio).  Cuando se alcanza,
    los splits adicionales generan una cadena de overflow buckets.

La API expuesta es la misma que usan las capas superiores:
    • build_index(...)
    • insert_record(IndexRecord)
    • search_record(key) → List[IndexRecord]
    • delete_record(key, offset=None)

Dependencias: utils.py, IndexRecord.py (ya existentes en el proyecto).
"""

import os
import struct
import pickle
from typing import Union, List, Tuple, BinaryIO, Any

from .IndexRecord import IndexRecord
from . import utils

__all__ = [
    "ExtendibleHashIndex",
]

# ------------------------------------------------
# auxiliares internos (reemplazan utilidades ausentes)
# ------------------------------------------------
def _empty_key(fmt: str):
    """Devuelve el valor-centinela para 'formato'."""
    return -1 if fmt == 'i' else (-1.0 if fmt == 'f' else '')

def _validate_type(val, fmt: str) -> bool:
    if fmt == 'i':
        return isinstance(val, int)
    if fmt == 'f':
        return isinstance(val, float)
    return isinstance(val, str)


###########################################################
# ---  Parámetros globales / auxiliares  ------------------
###########################################################
MAX_DEPTH_DEFAULT = 16          # profundidad global máxima (bits)
FB_DEFAULT        = 4           # Factor de bloqueo (registros por bucket)

###########################################################
# ---  Estructuras auxiliares  ----------------------------
###########################################################
class Bucket:
    """Bloque de registros con cabecera (size, next)."""

    HDR_FMT = "ii"               # size, next_bucket
    HDR_SIZE = struct.calcsize(HDR_FMT)

    def __init__(self, fb: int, key_fmt: str):
        self.fb        = fb
        self.key_fmt   = key_fmt
        self.size      = 0            # nº registros válidos
        self.next      = -1           # bucket de overflow o -1
        self.records: List[IndexRecord] = [
            IndexRecord(key_fmt, _empty_key(key_fmt), -1)
            for _ in range(fb)
        ]

    # ------------- serialización ------------------------------------
    def pack(self) -> bytes:
        data = b"".join(rec.pack() for rec in self.records)
        data += struct.pack(self.HDR_FMT, self.size, self.next)
        return data

    @classmethod
    def unpack(cls, buf: bytes, fb: int, key_fmt: str) -> "Bucket":
        bucket = cls(fb, key_fmt)
        bucket.size, bucket.next = struct.unpack_from(
            cls.HDR_FMT, buf, len(buf) - cls.HDR_SIZE
        )
        rec_size = bucket.records[0].size
        for i in range(bucket.size):
            off = i * rec_size
            bucket.records[i] = IndexRecord.unpack(buf[off : off + rec_size], key_fmt)
        return bucket

    # ------------- utilidades ---------------------------------------
    def is_full(self) -> bool:
        return self.size >= self.fb

    def add(self, rec: IndexRecord) -> None:
        if self.is_full():
            raise RuntimeError("Bucket lleno — use split/overflow")
        self.records[self.size] = rec
        self.size += 1

    def iter_valid(self):
        for i in range(self.size):
            yield self.records[i]

###########################################################
class DirNode:
    """Nodo interno del directorio binario (en memoria)."""

    __slots__ = ("left", "right", "left_leaf", "right_leaf")

    def __init__(self, left: Any = -1, right: Any = -1, leaf=True):
        self.left       = left
        self.right      = right
        self.left_leaf  = leaf
        self.right_leaf = leaf

    # --- navegación
    def next(self, bit: int) -> Tuple[Any, bool]:
        return (self.left, self.left_leaf) if bit == 0 else (self.right, self.right_leaf)

    # --- setters
    def set_child(self, bit: int, val: Any, leaf: bool):
        if bit == 0:
            self.left, self.left_leaf = val, leaf
        else:
            self.right, self.right_leaf = val, leaf

###########################################################
# ---  Implementación principal  --------------------------
###########################################################
class ExtendibleHashIndex:

    HDR_FMT  = "iiii"    # D, num_buckets, num_overflow, fb
    HDR_SIZE = struct.calcsize(HDR_FMT)

    # ---------------- constructor ----------------------
    def __init__(
        self,
        table_name: str,
        indexed_field: str,
        *,
        max_depth: int = MAX_DEPTH_DEFAULT,
        fb: int = FB_DEFAULT,
        create: bool = False,
    ):
        self.base = f"{table_name}.{indexed_field}.hash"
        self.data_path = self.base + ".idx"
        self.dir_path  = self.base + ".tree"
        self.max_depth = max_depth
        self.fb        = fb

        # cargar schema → determinar tipo de clave
        schema = utils.load_schema(table_name)
        self.key_fmt = utils.get_key_format_from_schema(schema, indexed_field)
        self.rec_size = IndexRecord(self.key_fmt, _empty_key(self.key_fmt), -1).size
        self.bucket_size = fb * self.rec_size + Bucket.HDR_SIZE

        if create:
            self._init_files()
        else:
            if not os.path.exists(self.data_path):
                raise FileNotFoundError("Índice no existe; use build_index() primero.")
            self._load_headers()

    # ---------------- inicialización -------------------
    def _init_files(self):
        """Crea archivos nuevos con D = 1 (dos buckets)."""
        self.D = 1
        self.num_buckets = 2      # base directory buckets (0,1)
        self.num_overflow = 0
        # crear archivo de datos
        with open(self.data_path, "wb") as f:
            f.write(struct.pack(self.HDR_FMT, self.D, self.num_buckets, self.num_overflow, self.fb))
            # bucket 0 & 1
            for _ in range(2):
                f.write(Bucket(self.fb, self.key_fmt).pack())
        # crear directorio (árbol con raíz apuntando a buckets 0/1)
        root = DirNode(0, 1)
        with open(self.dir_path, "wb") as df:
            pickle.dump(root, df)
        self.dir_root = root

    def _load_headers(self):
        with open(self.data_path, "rb") as f:
            self.D, self.num_buckets, self.num_overflow, self.fb = struct.unpack(self.HDR_FMT, f.read(self.HDR_SIZE))
        with open(self.dir_path, "rb") as df:
            self.dir_root = pickle.load(df)

    # ---------------- helpers de E/S --------------------
    def _bucket_offset(self, pos: int) -> int:
        return self.HDR_SIZE + pos * self.bucket_size

    def _read_bucket(self, fh: BinaryIO, pos: int) -> Bucket:
        fh.seek(self._bucket_offset(pos))
        return Bucket.unpack(fh.read(self.bucket_size), self.fb, self.key_fmt)

    def _write_bucket(self, fh: BinaryIO, pos: int, bucket: Bucket):
        fh.seek(self._bucket_offset(pos))
        fh.write(bucket.pack())

    def _flush_header(self, fh: BinaryIO):
        fh.seek(0)
        fh.write(struct.pack(self.HDR_FMT, self.D, self.num_buckets, self.num_overflow, self.fb))

    def _flush_dir(self):
        with open(self.dir_path, "wb") as df:
            pickle.dump(self.dir_root, df)

    # ---------------- hashing helpers ------------------
    def _hash(self, key) -> int:
        if self.key_fmt == 'i':
            return key & 0xFFFFFFFF
        if self.key_fmt == 'f':
            return int(abs(key) * 10_000) & 0xFFFFFFFF
        return sum(ord(c) for c in str(key)) & 0xFFFFFFFF

    def _dir_bits(self, hashed: int) -> List[int]:
        return [(hashed >> i) & 1 for i in range(self.D)][::-1]  # MSB→LSB list of length D

    # ---------------- API pública ----------------------
    @classmethod
    def build_index(cls, heap_path: str, extract_fn, field: str, *, fb: int = FB_DEFAULT, max_depth: int = MAX_DEPTH_DEFAULT):
        idx = cls(heap_path, field, fb=fb, max_depth=max_depth, create=True)
        for key, off in extract_fn(field):
            if _validate_type(key, idx.key_fmt):
                idx.insert_record(IndexRecord(idx.key_fmt, key, off))
        return idx

    # ---------------------------------------------------
    def insert_record(self, rec: IndexRecord):
        if rec.format != self.key_fmt:
            raise TypeError("Tipo de clave incorrecto para este índice")
        with open(self.data_path, "r+b") as fh:
            bucket_pos, bucket, path = self._find_bucket(fh, rec.key)
            # evitar duplicado exacto
            if any(r.key == rec.key and r.offset == rec.offset for r in bucket.iter_valid()):
                return
            if bucket.is_full():
                self._split_or_overflow(fh, path, bucket_pos, bucket, rec)
            else:
                bucket.add(rec)
                self._write_bucket(fh, bucket_pos, bucket)

    # ---------------- búsqueda -------------------------
    def search_record(self, key) -> List[IndexRecord]:
        if not _validate_type(key, self.key_fmt):
            raise TypeError("Clave no válida para este índice")
        res: List[IndexRecord] = []
        with open(self.data_path, "rb") as fh:
            pos, bucket, _ = self._find_bucket(fh, key)
            while True:
                for r in bucket.iter_valid():
                    if r.key == key:
                        res.append(r)
                if bucket.next == -1:
                    break
                bucket = self._read_bucket(fh, bucket.next)
        return res

    # ---------------- borrado --------------------------
    def delete_record(self, key, offset=None) -> bool:
        if not _validate_type(key, self.key_fmt):
            raise TypeError("Clave no válida")
        deleted = False
        with open(self.data_path, "r+b") as fh:
            pos, bucket, _ = self._find_bucket(fh, key)
            empty = IndexRecord(self.key_fmt, _empty_key(self.key_fmt), -1)
            while True:
                for i in range(bucket.size):
                    rec = bucket.records[i]
                    if rec.key == key and (offset is None or rec.offset == offset):
                        bucket.records[i] = empty
                        deleted = True
                self._write_bucket(fh, pos, bucket)
                if bucket.next == -1:
                    break
                pos = bucket.next
                bucket = self._read_bucket(fh, pos)
        return deleted

    # ---------------- impresión ------------------------
    def print_all(self):
        print(f"D={self.D}, buckets={self.num_buckets}, overflow={self.num_overflow}")
        with open(self.data_path, "rb") as fh:
            for pos in range(self.num_buckets + self.num_overflow):
                b = self._read_bucket(fh, pos)
                print(f"Bucket {pos} | size={b.size} next={b.next}")
                for r in b.iter_valid():
                    print("   ", r)

    ####################################################
    # --- funciones internas ---------------------------
    ####################################################
    def _find_bucket(self, fh: BinaryIO, key) -> Tuple[int, Bucket, List[Tuple[DirNode, int]]]:
        """Navega el directorio y devuelve (pos_bucket, bucket, path).
        *path* es una lista de (node, bit_tomado) para back‑tracking en splits.
        """
        hashed = self._hash(key)
        bits = self._dir_bits(hashed)
        node = self.dir_root
        path: List[Tuple[DirNode, int]] = []
        for bit in bits:
            nxt, is_leaf = node.next(bit)
            path.append((node, bit))
            if is_leaf:
                bucket_pos = nxt
                bucket = self._read_bucket(fh, bucket_pos)
                return bucket_pos, bucket, path
            node = nxt  # descender
        # sólo para mypy; flujo siempre retorna antes
        raise RuntimeError

    def _split_or_overflow(self, fh: BinaryIO, path, bucket_pos: int, bucket: Bucket, rec: IndexRecord):
        """Realiza split o crea overflow si D alcanzó MAX_DEPTH."""
        if self.D >= self.max_depth:
            self._add_overflow(fh, bucket_pos, bucket, rec)
            return
        # -------- split --------
        new_bucket_pos = self.num_buckets + self.num_overflow
        new_bucket = Bucket(self.fb, self.key_fmt)
        # mover registros + nuevo
        all_recs = list(bucket.iter_valid()) + [rec]
        bucket.size = 0
        bucket.next = -1
        for r in all_recs:
            target = bucket if self._bit_for_key(r.key) == 0 else new_bucket
            target.add(r)
        # actualizar directorio (último nodo del path)
        parent, bit = path[-1]
        new_node = DirNode(bucket_pos, new_bucket_pos)
        parent.set_child(bit, new_node, leaf=False)
        # actualizar metadatos y persistir
        self.num_buckets += 1
        self.D += 1 if self.num_buckets > (1 << self.D) else 0
        self._flush_dir()
        self._flush_header(fh)
        self._write_bucket(fh, bucket_pos, bucket)
        self._write_bucket(fh, new_bucket_pos, new_bucket)

    def _add_overflow(self, fh: BinaryIO, pos: int, bucket: Bucket, rec: IndexRecord):
        """Cuelga un overflow bucket al final de la cadena."""
        while bucket.next != -1:
            pos = bucket.next
            bucket = self._read_bucket(fh, pos)
        if bucket.is_full():
            new_pos = self.num_buckets + self.num_overflow
            ov = Bucket(self.fb, self.key_fmt)
            ov.add(rec)
            bucket.next = new_pos
            self._write_bucket(fh, pos, bucket)
            self._write_bucket(fh, new_pos, ov)
            self.num_overflow += 1
            self._flush_header(fh)
        else:
            bucket.add(rec)
            self._write_bucket(fh, pos, bucket)

    def _bit_for_key(self, key) -> int:
        return (self._hash(key) >> (self.max_depth - 1)) & 1  # MSB relevante
