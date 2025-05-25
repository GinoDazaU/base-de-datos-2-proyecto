import os
import json
import math
from typing import List, Dict, Any, Union

from .IndexRecord import IndexRecord
from . import utils

# ---------------------------------------------------------------------------
#  Parámetros globales del índice hash extensible
# ---------------------------------------------------------------------------
GLOBAL_DEPTH: int = 16   # profundidad máxima permitida del directorio
BUCKET_FACTOR: int = 4   # capacidad máxima de registros por bucket

# ---------------------------------------------------------------------------
#  Valores centinela (registros "borrados")
# ---------------------------------------------------------------------------
SENTINEL_INT = -1
SENTINEL_FLOAT = -1.0
SENTINEL_STR = ""

def _sentinel(fmt: str):
    if fmt == "i":
        return SENTINEL_INT
    if fmt == "f":
        return SENTINEL_FLOAT
    if "s" in fmt:
        return SENTINEL_STR
    raise ValueError(f"Formato no soportado: {fmt}")

# ---------------------------------------------------------------------------
#  Clase principal
# ---------------------------------------------------------------------------
class ExtendibleHashIndex:
    """Índice hash extensible persistente en JSON.

    Formato de archivo (pretty‑printed para legibilidad):

    {
      "global_depth": 1,
      "bucket_factor": 4,
      "key_format": "10s",
      "directory": [0, 0],          # 2 ** global_depth entries
      "buckets": {
        "0": {"depth": 1, "records": [["ana", 15], ["bob", 7]]}
      }
    }
    """

    # ------------------------------------------------------------------
    #  Construcción inicial --------------------------------------------
    # ------------------------------------------------------------------
    @staticmethod
    def build_index(base_filename: str, extract_index_fn, key_field: str) -> None:
        """Crea / recrea el archivo *.hash.idx para *key_field* a partir
        de los valores actuales del `HeapFile`.
        """
        schema = utils.load_schema(base_filename)
        key_fmt = utils.get_key_format_from_schema(schema, key_field)

        idx_filename = f"{base_filename}.{key_field}.hash.idx"
        if os.path.exists(idx_filename):
            os.remove(idx_filename)

        # --- 1) Estado mínimo ---------------------------------------
        state = {
            "global_depth": 1,
            "bucket_factor": BUCKET_FACTOR,
            "key_format": key_fmt,
            "directory": [0, 0],           # 2 ** 1
            "buckets": {
                "0": {"depth": 1, "records": []}
            }
        }
        with open(idx_filename, "w", encoding="utf-8") as jf:
            json.dump(state, jf, indent=2)

        # --- 2) Insertar todas las entradas existentes --------------
        idx = ExtendibleHashIndex(base_filename, key_field)
        for key, off in extract_index_fn(key_field):
            if not ExtendibleHashIndex._validate_type(key, key_fmt):
                continue
            idx.insert_record(IndexRecord(key_fmt, key, off))

    # ------------------------------------------------------------------
    #  Inicialización de instancia -------------------------------------
    # ------------------------------------------------------------------
    def __init__(self, base_filename: str, key_field: str):
        self.filename = f"{base_filename}.{key_field}.hash.idx"
        if not os.path.exists(self.filename):
            raise FileNotFoundError(
                f"Índice inexistente: {self.filename}. Crea el índice con create_hash_idx().")
        with open(self.filename, "r", encoding="utf-8") as jf:
            self._state: Dict[str, Any] = json.load(jf)

        self.key_format: str = self._state["key_format"]
        self.bucket_factor: int = self._state["bucket_factor"]

    # ------------------------------------------------------------------
    #  API pública ------------------------------------------------------
    # ------------------------------------------------------------------
    def insert_record(self, record: IndexRecord) -> None:
        if record.format != self.key_format:
            raise TypeError("Formato de clave incompatible con el índice")
        self._insert_in_memory(record)
        self._persist()

    def search_record(self, key: Union[int, float, str]):
        if not self._validate_type(key, self.key_format):
            raise TypeError("Tipo de clave incorrecto")
        dir_idx = self._directory_index(key)
        bucket_id = self._state["directory"][dir_idx]
        bucket = self._state["buckets"][str(bucket_id)]
        return [IndexRecord(self.key_format, k, off) for k, off in bucket["records"] if k == key]

    def delete_record(self, key, offset):
        if not self._validate_type(key, self.key_format):
            raise TypeError("Tipo de clave incorrecto")
        dir_idx = self._directory_index(key)
        bucket = self._state["buckets"][str(self._state["directory"][dir_idx])]
        for i, (k, off) in enumerate(bucket["records"]):
            if k == key and off == offset:
                del bucket["records"][i]
                self._persist()
                return True
        return False

    def print_all(self):
        print(json.dumps(self._state, indent=2))

    # ------------------------------------------------------------------
    #  Internals --------------------------------------------------------
    # ------------------------------------------------------------------
    @staticmethod
    def _validate_type(val, fmt):
        if fmt == "i":
            return isinstance(val, int)
        if fmt == "f":
            return isinstance(val, float)
        if "s" in fmt:
            return isinstance(val, str)
        return False

    def _hash(self, key):
        h = hash(key)
        if isinstance(key, float):
            h = hash(round(key, 10))
        return h & ((1 << GLOBAL_DEPTH) - 1)

    def _directory_index(self, key):
        gd = self._state["global_depth"]
        return self._hash(key) & ((1 << gd) - 1)

    def _insert_in_memory(self, rec: IndexRecord):
        while True:
            dir_idx = self._directory_index(rec.key)
            bucket_id = self._state["directory"][dir_idx]
            bucket = self._state["buckets"][str(bucket_id)]

            # Duplicado exacto
            if any(k == rec.key and off == rec.offset for k, off in bucket["records"]):
                return

            # Espacio libre
            if len(bucket["records"]) < self.bucket_factor:
                bucket["records"].append([rec.key, rec.offset])
                return

            # Necesario split
            if bucket["depth"] == GLOBAL_DEPTH:
                raise RuntimeError("Se alcanzó la profundidad máxima global")

            # Si LD == GD implica duplicar directorio
            if bucket["depth"] == self._state["global_depth"]:
                self._double_directory()
                # recalcular después de aumentar GD
                continue

            self._split_bucket(bucket_id)
            # repetirá el ciclo con nueva distribución

    def _double_directory(self):
        self._state["directory"].extend(self._state["directory"])
        self._state["global_depth"] += 1

    def _split_bucket(self, bucket_id: int):
        bucket = self._state["buckets"][str(bucket_id)]
        old_depth = bucket["depth"]
        new_depth = old_depth + 1
        bucket["depth"] = new_depth

        # Crear nuevo bucket
        new_bucket_id = str(max(int(b) for b in self._state["buckets"].keys()) + 1)
        self._state["buckets"][new_bucket_id] = {"depth": new_depth, "records": []}

        # Actualizar directorio
        gd = self._state["global_depth"]
        for i in range(1 << gd):
            if self._state["directory"][i] != bucket_id:
                continue
            if (i >> (new_depth - 1)) & 1:  # bit significativo para el nuevo nivel
                self._state["directory"][i] = int(new_bucket_id)

        # Reinsertar registros
        old_records = bucket["records"]
        bucket["records"] = []
        for k, off in old_records:
            self._insert_in_memory(IndexRecord(self.key_format, k, off))

    # ------------------------------------------------------------------
    #  Persistencia -----------------------------------------------------
    # ------------------------------------------------------------------
    def _persist(self):
        with open(self.filename, "w", encoding="utf-8") as jf:
            json.dump(self._state, jf, indent=2)
