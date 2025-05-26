import os
import pickle
from typing import List, Union, Dict, Any

from .IndexRecord import IndexRecord
from . import utils

__all__ = ["ExtendibleHashIndex"]

class ExtendibleHashIndex:
    """Índice Hash Extensible persistido en **un solo archivo binario** usando ``pickle``.

    El nombre del archivo sigue el convenio:

    ``{table_path}.{field_name}.hash.idx``

    - ``__init__(table_path, field_name)``  → carga el índice
    - ``build_index(table_path, extract_fn, field_name)`` → (re)construye
    - ``insert_record(IndexRecord)``
    - ``search_record(key)``
    - ``delete_record(key, offset)``
    - ``print_all()``

    Internamente mantiene:

    - ``global_depth``: bits examinados del hash
    - ``directory``   : lista que mapea a ``bucket_id``
    - ``buckets``     : lista de buckets (cada uno con ``local_depth`` y ``records``)

    Cada bucket contiene como máximo ``BUCKET_FACTOR`` registros antes de dividirse.
    """

    GLOBAL_DEPTH: int = 16           # profundidad máxima permitida
    BUCKET_FACTOR: int = 4           # máx. registros por bucket

    SENTINEL_INT = -1
    SENTINEL_STR = ""

    # ------------------------------------------------------------------
    #  API pública ------------------------------------------------------
    # ------------------------------------------------------------------

    def __init__(self, table_path: str, field_name: str):
        self.table_path = table_path
        self.field_name = field_name
        self.filename = f"{table_path}.{field_name}.hash.idx"

        if not os.path.exists(self.filename):
            raise FileNotFoundError(f"Índice hash no encontrado: {self.filename}")
        self._load()

    # ---------------------- Consultas ----------------------------------

    def search_record(self, key: Union[int, str]) -> List[IndexRecord]:
        """Devuelve una lista (posiblemente vacía) de ``IndexRecord`` con esa clave."""
        if not self._validate_type(key):
            raise TypeError(f"Clave {key!r} no coincide con formato '{self.key_format}'.")

        bucket = self._bucket_for_key(key)
        out: List[IndexRecord] = []
        for rec in bucket['records']:
            if rec['key'] == key:
                out.append(IndexRecord(self.key_format, rec['key'], rec['offset']))
        return out

    # ---------------------- Inserción -----------------------------------

    def insert_record(self, idx_rec: IndexRecord) -> None:
        if idx_rec.format != self.key_format:
            raise TypeError("Formato de IndexRecord no coincide con el índice.")
        if self._is_sentinel(idx_rec.key):
            return
        self._insert_internal(idx_rec)
        self._save()

    # ---------------------- Borrado -------------------------------------

    def delete_record(self, key: Union[int, str], offset: int) -> bool:
        if not self._validate_type(key):
            raise TypeError("Tipo de clave incorrecto para el índice hash.")
        bucket = self._bucket_for_key(key)
        before = len(bucket['records'])
        bucket['records'] = [r for r in bucket['records'] if not (r['key'] == key and r['offset'] == offset)]
        found = len(bucket['records']) < before
        if found:
            self._save()
        return found

    # ---------------------- Debug --------------------------------------

    def print_all(self):
        print(f"FILE: {self.filename}")
        print(f"GlobalDepth={self.global_depth}  BucketFactor={self.BUCKET_FACTOR}  Format='{self.key_format}'")
        print("-" * 60)
        for i, bid in enumerate(self.directory):
            print(f"Dir[{i:0{self.global_depth}b}] -> Bucket {bid}")
        print("\nBuckets:")
        for bid, b in enumerate(self.buckets):
            print(f"  Bucket {bid}: local_depth={b['local_depth']} size={len(b['records'])}")
            for rec in b['records']:
                print(f"    {rec['key']!r} -> {rec['offset']}")
        print("=" * 60)

    # ------------------------------------------------------------------
    #  Creación estática ------------------------------------------------
    # ------------------------------------------------------------------

    @staticmethod
    def build_index(table_path: str, extract_index_fn, key_field: str):
        """Reconstruye el índice a partir de los datos actuales del HeapFile."""
        schema = utils.load_schema(table_path)
        key_format = utils.get_key_format_from_schema(schema, key_field)
        if key_format not in ('i',) and 's' not in key_format:
            raise ValueError("ExtendibleHashIndex solo soporta int o string.")

        idx = ExtendibleHashIndex._new_empty(table_path, key_field, key_format)

        for key, offset in extract_index_fn(key_field):
            if idx._is_sentinel(key):
                continue
            if not idx._validate_type(key):
                continue
            idx._insert_internal(IndexRecord(key_format, key, offset))

        idx._save()
        return True

    # ------------------------------------------------------------------
    #  Implementación interna ------------------------------------------
    # ------------------------------------------------------------------

    @classmethod
    def _new_empty(cls, table_path: str, field_name: str, key_format: str):
        instance = object.__new__(cls)
        instance.table_path = table_path
        instance.field_name = field_name
        instance.filename = f"{table_path}.{field_name}.hash.idx"
        instance.key_format = key_format
        instance.global_depth = 1  # directorio con 2 entradas iniciales
        instance.directory = [0, 0]
        instance.buckets: List[Dict[str, Any]] = [{
            'local_depth': 1,
            'records': []
        }]
        return instance

    # ---------------------- Helpers ------------------------------------

    def _validate_type(self, key) -> bool:
        if self.key_format == 'i':
            return isinstance(key, int)
        if 's' in self.key_format:
            return isinstance(key, str)
        return False

    def _is_sentinel(self, key) -> bool:
        if self.key_format == 'i':
            return key == self.SENTINEL_INT
        return key == self.SENTINEL_STR

    def _hash_key(self, key: Union[int, str]) -> int:
        if self.key_format == 'i':
            return key & 0xFFFFFFFF
        h = 0
        for ch in key:
            h = ((h * 31) + ord(ch)) & 0xFFFFFFFF
        return h

    def _bucket_index(self, key) -> int:
        mask = (1 << self.global_depth) - 1
        return self._hash_key(key) & mask

    def _bucket_for_key(self, key):
        return self.buckets[self.directory[self._bucket_index(key)]]

    def _insert_internal(self, idx_rec: IndexRecord):
        while True:
            dir_idx = self._bucket_index(idx_rec.key)
            bucket_id = self.directory[dir_idx]
            bucket = self.buckets[bucket_id]

            # espacio libre ⇒ insertamos
            if len(bucket['records']) < self.BUCKET_FACTOR:
                bucket['records'].append({'key': idx_rec.key, 'offset': idx_rec.offset})
                return

            # bucket lleno, ver si podemos dividir
            if bucket['local_depth'] == self.GLOBAL_DEPTH:
                # overflow sin dividir más (insertamos de todos modos)
                bucket['records'].append({'key': idx_rec.key, 'offset': idx_rec.offset})
                return

            # dividir bucket
            self._split_bucket(bucket_id)
            # e intentar de nuevo (loop)

    def _split_bucket(self, bucket_id: int):
        old_bucket = self.buckets[bucket_id]
        old_ld = old_bucket['local_depth']
        new_ld = old_ld + 1
        old_bucket['local_depth'] = new_ld

        # crear bucket nuevo
        new_bucket_id = len(self.buckets)
        new_bucket = {'local_depth': new_ld, 'records': []}
        self.buckets.append(new_bucket)

        # duplicar directorio si hace falta
        if new_ld > self.global_depth:
            if self.global_depth >= self.GLOBAL_DEPTH:
                return  # alcanzamos límite teórico
            self.directory.extend(self.directory)
            self.global_depth += 1

        # reasignar entradas del directorio
        for i in range(len(self.directory)):
            if self.directory[i] == bucket_id and ((i >> (new_ld - 1)) & 1):
                self.directory[i] = new_bucket_id

        # reubicar registros
        moved = []
        for rec in old_bucket['records']:
            idx = self._bucket_index(rec['key'])
            dest_bucket = self.buckets[self.directory[idx]]
            if dest_bucket is not old_bucket:
                moved.append(rec)
                dest_bucket['records'].append(rec)
        for rec in moved:
            old_bucket['records'].remove(rec)

    # --------------------- Persistencia --------------------------------

    def _save(self):
        data = {
            'key_format': self.key_format,
            'global_depth': self.global_depth,
            'directory': self.directory,
            'buckets': self.buckets
        }
        with open(self.filename, 'wb') as fh:
            pickle.dump(data, fh, protocol=pickle.HIGHEST_PROTOCOL)

    def _load(self):
        with open(self.filename, 'rb') as fh:
            data = pickle.load(fh)
        self.key_format = data['key_format']
        self.global_depth = data['global_depth']
        self.directory = data['directory']
        self.buckets = data['buckets']
