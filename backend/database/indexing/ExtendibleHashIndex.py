import os
import json
from typing import List, Dict, Any, Union

from .IndexRecord import IndexRecord
from . import utils


class ExtendibleHashIndex:
    """Índice Hash Extensible (directory + buckets).

    ▸ Directorio:   2^global_depth entradas → id de bucket.
    ▸ Bucket:       lista de IndexRecord (hasta BUCKET_FACTOR) + local_depth.

    El índice se persiste en un único archivo JSON con la extensión
    ".hash.idx".  Para un nombre base `table_path` y campo `field_name`, el
    archivo se llama:

        table_path + "." + field_name + ".hash.idx"

    Solo se soportan claves *int* y *string* (el formato se obtiene del schema
    de la tabla).
    """

    GLOBAL_DEPTH: int = 16        # Profundidad máxima del directorio (2^16)
    BUCKET_FACTOR: int = 4        # Máx. registros por bucket antes de dividir

    SENTINEL_INT = -1
    SENTINEL_STR = ""

    # ------------------------------------------------------------------
    #  API pública -------------------------------------------------------
    # ------------------------------------------------------------------

    def __init__(self, table_path: str, field_name: str):
        self.table_path = table_path
        self.field_name = field_name
        self.filename = f"{table_path}.{field_name}.hash.idx"

        if not os.path.exists(self.filename):
            raise FileNotFoundError(f"Índice hash no encontrado: {self.filename}.")

        self._load()

    # ...................... Operaciones de consulta ...................

    def search_record(self, key: Union[int, str]) -> List[IndexRecord]:
        """Devuelve todos los IndexRecord cuyo key == *key* (lista vacía si no hay)."""
        if not self._validate_type(key):
            raise TypeError(f"Clave {key!r} no coincide con formato '{self.key_format}'.")

        bucket_idx = self._bucket_index(key)
        bucket = self.buckets[self.directory[bucket_idx]]
        return [IndexRecord(self.key_format, rec['key'], rec['offset'])
                for rec in bucket['records']
                if rec['key'] == key]

    # ...................... Operaciones de inserción ..................

    def insert_record(self, idx_rec: IndexRecord) -> None:
        if idx_rec.format != self.key_format:
            raise TypeError("Formato de IndexRecord no coincide con el índice.")
        if self._is_sentinel(idx_rec.key):
            return  # no indexamos centinelas

        self._insert_internal(idx_rec)
        self._save()

    # ...................... Operaciones de borrado ....................

    def delete_record(self, key: Union[int, str], offset: int) -> bool:
        """Elimina el par (key, offset).  Devuelve True si lo encontró."""
        if not self._validate_type(key):
            raise TypeError("Tipo de clave incorrecto.")

        bucket_idx = self._bucket_index(key)
        bucket = self.buckets[self.directory[bucket_idx]]
        before = len(bucket['records'])
        bucket['records'] = [rec for rec in bucket['records']
                              if not (rec['key'] == key and rec['offset'] == offset)]
        found = len(bucket['records']) < before
        if found:
            self._save()
        return found

    # ...................... Debug / inspección ........................

    def print_all(self) -> None:
        print(f"FILE: {self.filename}")
        print(f"GlobalDepth={self.global_depth}  BucketFactor={self.BUCKET_FACTOR}  Format='{self.key_format}'")
        print("-" * 60)
        for i, bucket_id in enumerate(self.directory):
            print(f"Dir[{i:>5b}]: → Bucket {bucket_id}")
        print("\nBuckets:")
        for bid, bucket in enumerate(self.buckets):
            print(f"  Bucket {bid}: local_depth={bucket['local_depth']}  size={len(bucket['records'])}")
            for rec in bucket['records']:
                print(f"    {rec['key']!r} -> {rec['offset']}")
        print("=" * 60)

    # ------------------------------------------------------------------
    #  Creación (estático) ----------------------------------------------
    # ------------------------------------------------------------------

    @staticmethod
    def build_index(table_path: str, extract_index_fn, key_field: str):
        """Reconstruye el índice a partir de los datos actuales del HeapFile."""
        # ---- determinar formato de clave ----
        schema = utils.load_schema(table_path)
        key_format = utils.get_key_format_from_schema(schema, key_field)
        if key_format not in ('i',) and 's' not in key_format:
            raise ValueError("ExtendibleHashIndex solo soporta int o string.")

        idx = ExtendibleHashIndex._new_empty(table_path, key_field, key_format)

        # ---- insertar (key, offset) de la tabla ----
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
        """Crea un índice vacío (1 bucket, global_depth=1) y lo devuelve sin guardar."""
        instance = object.__new__(cls)
        instance.table_path = table_path
        instance.field_name = field_name
        instance.filename = f"{table_path}.{field_name}.hash.idx"

        instance.key_format = key_format
        instance.global_depth = 1  # directorio de 2 entradas
        instance.directory = [0, 0]
        instance.buckets = [{
            'local_depth': 1,
            'records': []
        }]
        return instance

    # ............................... Helpers ...........................

    def _validate_type(self, key) -> bool:
        if self.key_format == 'i':
            return isinstance(key, int)
        # formato 'Ns' (string fijo)
        if 's' in self.key_format:
            return isinstance(key, str)
        return False

    def _is_sentinel(self, key) -> bool:
        if self.key_format == 'i':
            return key == self.SENTINEL_INT
        else:
            return key == self.SENTINEL_STR

    def _hash_key(self, key: Union[int, str]) -> int:
        """Hash determinístico (32‑bit) para int o str."""
        if self.key_format == 'i':
            return key & 0xFFFFFFFF
        # simple hash para string (polynomial rolling)
        h = 0
        for ch in key:
            h = ((h * 31) + ord(ch)) & 0xFFFFFFFF
        return h

    def _bucket_index(self, key) -> int:
        mask = (1 << self.global_depth) - 1
        return self._hash_key(key) & mask

    def _insert_internal(self, idx_rec: IndexRecord):
        """Inserción *en memoria* (sin guardar)."""
        while True:
            dir_idx = self._bucket_index(idx_rec.key)
            bucket_id = self.directory[dir_idx]
            bucket = self.buckets[bucket_id]

            # --- insertar si hay espacio ----
            if len(bucket['records']) < self.BUCKET_FACTOR:
                bucket['records'].append({
                    'key': idx_rec.key,
                    'offset': idx_rec.offset
                })
                return

            # --- bucket lleno ----
            if bucket['local_depth'] == self.GLOBAL_DEPTH:
                # No podemos dividir más: usar overflow (sin límite)
                bucket['records'].append({
                    'key': idx_rec.key,
                    'offset': idx_rec.offset
                })
                return

            # ---- dividir bucket ----
            self._split_bucket(bucket_id)
            # loop nuevamente para reubicar idx_rec

    def _split_bucket(self, bucket_id: int):
        old_bucket = self.buckets[bucket_id]
        old_ld = old_bucket['local_depth']
        new_ld = old_ld + 1
        old_bucket['local_depth'] = new_ld

        # Crear bucket nuevo
        new_bucket_id = len(self.buckets)
        new_bucket = {
            'local_depth': new_ld,
            'records': []
        }
        self.buckets.append(new_bucket)

        # Duplicar directorio si es necesario
        if new_ld > self.global_depth:
            if self.global_depth >= self.GLOBAL_DEPTH:
                return  # no deberíamos ocurrir porque chequeamos antes
            self.directory = self.directory + self.directory
            self.global_depth += 1

        # Reasignar entradas del directorio
        for i in range(len(self.directory)):
            if self.directory[i] == bucket_id:
                if ((i >> (new_ld - 1)) & 1):
                    self.directory[i] = new_bucket_id

        # Reinsertar registros del bucket antiguo (puede mover algunos)
        old_records = old_bucket['records']
        old_bucket['records'] = []
        for rec in old_records:
            key, offset = rec['key'], rec['offset']
            dir_idx = self._bucket_index(key)
            dest_bucket = self.buckets[self.directory[dir_idx]]
            dest_bucket['records'].append(rec)

    # .......................... Persistencia ...........................

    def _load(self):
        with open(self.filename, 'r', encoding='utf-8') as fh:
            data = json.load(fh)
        self.key_format = data['key_format']
        self.global_depth = data['global_depth']
        self.directory = data['directory']
        self.buckets = data['buckets']

    def _save(self):
        data = {
            'key_format': self.key_format,
            'global_depth': self.global_depth,
            'directory': self.directory,
            'buckets': self.buckets
        }
        with open(self.filename, 'w', encoding='utf-8') as fh:
            json.dump(data, fh)
