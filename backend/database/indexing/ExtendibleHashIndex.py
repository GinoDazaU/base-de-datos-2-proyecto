
"""
Implementación de un Índice Hash Extensible en disco, compatible con database.py.

Estructura de archivos:
- {table}.{field}.hash.idx   → Archivo marcador (para database.py)
- {table}.{field}.hash.db    → Buckets binarios fijos
- {table}.{field}.hash.tree  → Árbol binario serializado con pickle
"""

from __future__ import annotations
import os, struct, pickle, hashlib
from typing import List, Union
from .IndexRecord import IndexRecord
from . import utils

# Constantes globales para el hash extensible
global_depth = 16         # bits de hash usados (2^16 entradas posibles)
bucket_factor = 4         # cantidad máxima de registros por bucket
sentinel_int = -1
sentinel_str = ""

# ================================
# Clase interna: Registro sencillo
# ================================
class _Rec:
    __slots__ = ("key", "offset")
    def __init__(self, key, offset):
        self.key, self.offset = key, offset
    def to_bytes(self):
        return pickle.dumps((self.key, self.offset))
    @classmethod
    def from_bytes(cls, blob):
        return cls(*pickle.loads(blob))

# ===============================================
# Clase interna: Bucket (almacenado fijo en disco)
# ===============================================
class _Bucket:
    HDR_FMT = "!ii8s"   # num_registros, siguiente_bucket, padding
    HDR_SIZE = struct.calcsize(HDR_FMT)

    def __init__(self, bid: int, cap: int, fm: _FileMgr):
        self.bid = bid; self.cap = cap; self.fm = fm
        self.next_bid = -1
        self.records: List[_Rec] = []

    def _raw(self):
        return self.fm._read_raw(self.bid)

    def _write(self, blob):
        self.fm._write_raw(self.bid, blob)

    def load(self):
        blob = self._raw()
        n, nxt, _ = struct.unpack(self.HDR_FMT, blob[:self.HDR_SIZE])
        self.next_bid = nxt
        self.records.clear()
        p = self.HDR_SIZE
        for _ in range(n):
            ln = struct.unpack("!I", blob[p:p+4])[0]; p += 4
            rec_blob = blob[p:p+ln]; p += ln
            self.records.append(_Rec.from_bytes(rec_blob))

    def save(self):
        body = b"".join(struct.pack("!I", len(r.to_bytes())) + r.to_bytes() for r in self.records)
        hdr = struct.pack(self.HDR_FMT, len(self.records), self.next_bid, b"\x00"*8)
        self._write(hdr + body)

    def is_full(self):
        return len(self.records) >= self.cap

    def insert(self, rec: _Rec):
        self.load()
        if not self.is_full():
            self.records.append(rec); self.save(); return True
        if self.next_bid != -1:
            return self.fm.bucket(self.next_bid).insert(rec)
        return False

    def search(self, key):
        self.load()
        for r in self.records:
            if r.key == key: return r
        return None if self.next_bid == -1 else self.fm.bucket(self.next_bid).search(key)

    def delete(self, key):
        self.load()
        for i, r in enumerate(self.records):
            if r.key == key:
                del self.records[i]; self.save(); return True
        if self.next_bid == -1: return False
        deleted = self.fm.bucket(self.next_bid).delete(key)
        if deleted and not self.fm.bucket(self.next_bid)._has_data():
            nb = self.fm.bucket(self.next_bid)
            self.next_bid = nb.next_bid
            self.save()
        return deleted

    def get_all(self):
        self.load()
        out = list(self.records)
        if self.next_bid != -1:
            out.extend(self.fm.bucket(self.next_bid).get_all())
        return out

    def _has_data(self):
        self.load()
        return bool(self.records) or self.next_bid != -1

# ==========================================
# Manejador de buckets en disco (I/O binario)
# ==========================================
class _FileMgr:
    HDR_FMT = "!ii8s"
    HDR_SIZE = struct.calcsize(HDR_FMT)

    def __init__(self, path: str, cap: int):
        self.path, self.cap = path, cap
        if not os.path.exists(path):
            with open(path, "wb") as f:
                f.write(struct.pack(self.HDR_FMT, 0, self.cap, b"\x00"*8))
            self.next_bid = 0
        else:
            with open(path, "rb") as f:
                self.next_bid, self.cap, _ = struct.unpack(self.HDR_FMT, f.read(self.HDR_SIZE))

    def _bucket_size(self):
        avg = 128
        return _Bucket.HDR_SIZE + self.cap * (4 + avg)

    def _offset(self, bid):
        return self.HDR_SIZE + bid * self._bucket_size()

    def _read_raw(self, bid):
        with open(self.path, "rb") as f:
            f.seek(self._offset(bid)); return f.read(self._bucket_size())

    def _write_raw(self, bid, data):
        data = data.ljust(self._bucket_size(), b"\x00")
        with open(self.path, "r+b") as f:
            f.seek(self._offset(bid)); f.write(data)

    def create_bucket(self):
        bid = self.next_bid; self.next_bid += 1; self._write_header()
        b = _Bucket(bid, self.cap, self)
        b.save(); return b

    def bucket(self, bid): return _Bucket(bid, self.cap, self)

    def _write_header(self):
        with open(self.path, "r+b") as f:
            f.seek(0)
            f.write(struct.pack(self.HDR_FMT, self.next_bid, self.cap, b"\x00"*8))

# ==============================================
# Nodo de árbol binario (bitwise trie del hash)
# ==============================================
class _Node:
    __slots__ = ("level", "left", "right", "bid")
    def __init__(self, level:int, bid:int):
        self.level = level; self.left = self.right = None; self.bid = bid
    def is_leaf(self): return self.left is None

# ==============================================
# Implementación del árbol hash extensible
# ==============================================
class _HashTree:
    def __init__(self, base_path: str, key_format: str):
        self.base = base_path
        self.db_path = f"{base_path}.hash.db"
        self.tree_path = f"{base_path}.hash.tree"
        self.kfmt = key_format
        self.fm = _FileMgr(self.db_path, bucket_factor)
        if os.path.exists(self.tree_path):
            with open(self.tree_path, "rb") as fh:
                self.root = pickle.load(fh)
        else:
            b0 = self.fm.create_bucket(); b1 = self.fm.create_bucket()
            self.root = _Node(0, None)
            self.root.left  = _Node(1, b0.bid)
            self.root.right = _Node(1, b1.bid)
            self._save()

    def _save(self):
        with open(self.tree_path, "wb") as fh: pickle.dump(self.root, fh)

    def _hash_bits(self, key):
        if isinstance(key, str):
            h = int.from_bytes(hashlib.sha256(key.encode()).digest(), "little")
        else:
            h = key & 0xFFFFFFFF
        return format(h, f"0{global_depth}b")

    def _leaf(self, bits):
        n = self.root
        while not n.is_leaf():
            n = n.left if bits[n.level] == "0" else n.right
        return n

    def insert(self, key, offset):
        rec = _Rec(key, offset)
        bits = self._hash_bits(key)
        leaf = self._leaf(bits)
        bucket = self.fm.bucket(leaf.bid)
        if bucket.insert(rec): return
        if leaf.level >= global_depth - 1:
            ov = self.fm.create_bucket()
            bucket.load(); bucket.next_bid = ov.bid; bucket.save()
            ov.insert(rec); return
        self._split(leaf, rec)

    def _split(self, leaf:_Node, rec:_Rec=None):
        bucket = self.fm.bucket(leaf.bid)
        todo = bucket.get_all()
        if rec: todo.append(rec)
        left_b = self.fm.create_bucket(); right_b = self.fm.create_bucket()
        leaf.left  = _Node(leaf.level+1, left_b.bid)
        leaf.right = _Node(leaf.level+1, right_b.bid)
        leaf.bid   = None
        for r in todo:
            dest = leaf.left if self._hash_bits(r.key)[leaf.level]=="0" else leaf.right
            self.fm.bucket(dest.bid).insert(r)
        self._save()

    def search(self, key):
        bits = self._hash_bits(key)
        bucket = self.fm.bucket(self._leaf(bits).bid)
        r = bucket.search(key)
        return [] if r is None else [r.offset]

    def delete(self, key):
        bits = self._hash_bits(key)
        bucket = self.fm.bucket(self._leaf(bits).bid)
        bucket.delete(key)
        self._save()

    def all_records(self):
        res=[]
        def dfs(n:_Node):
            if n.is_leaf(): res.extend(self.fm.bucket(n.bid).get_all())
            else: dfs(n.left); dfs(n.right)
        dfs(self.root); return res

# ==============================================
# Interfaz principal compatible con database.py
# ==============================================
class ExtendibleHashIndex:
    def __init__(self, table_path: str, field_name: str):
        self.idx_file = f"{table_path}.{field_name}.hash.idx"
        if not os.path.exists(self.idx_file):
            raise FileNotFoundError(f"\u00cdndice hash no encontrado: {self.idx_file}")
        schema = utils.load_schema(table_path)
        self.kfmt = utils.get_key_format_from_schema(schema, field_name)
        self.tree = _HashTree(f"{table_path}.{field_name}", self.kfmt)

    def search_record(self, key) -> List[IndexRecord]:
        self._check_type(key)
        offsets = self.tree.search(key)
        return [IndexRecord(self.kfmt, key, off) for off in offsets]

    def insert_record(self, idx_rec: IndexRecord):
        if idx_rec.format != self.kfmt:
            raise TypeError("Formato de clave no coincide.")
        if self._is_sentinel(idx_rec.key):
            return
        self.tree.insert(idx_rec.key, idx_rec.offset)

    def delete_record(self, key, offset) -> bool:
        self._check_type(key)
        self.tree.delete(key)
        return True

    def print_all(self):
        for r in sorted(self.tree.all_records(), key=lambda x: x.key):
            print(f"{r.key!r} -> {r.offset}")

    @staticmethod
    def build_index(table_path: str, extract_fn, field_name: str):
        schema = utils.load_schema(table_path)
        kfmt = utils.get_key_format_from_schema(schema, field_name)
        tree = _HashTree(f"{table_path}.{field_name}", kfmt)
        for key, offset in extract_fn(field_name):
            if key == (sentinel_int if kfmt=='i' else sentinel_str): continue
            tree.insert(key, offset)
        tree._save()
        open(f"{table_path}.{field_name}.hash.idx", "wb").close()
        return True

    def _check_type(self, key):
        if (self.kfmt=='i' and not isinstance(key,int)) or ('s' in self.kfmt and not isinstance(key,str)):
            raise TypeError("Tipo de clave no coincide con formato del índice.")

    def _is_sentinel(self, key):
        return key == (sentinel_int if self.kfmt=='i' else sentinel_str)
