import struct
import json
import os
from typing import Optional, Tuple, List

from .Record import Record

# --------------------------------------------------------
#  Valores centinela para marcar registros eliminados
# --------------------------------------------------------
SENTINEL_INT: int = -1                 # Para campos int / long
SENTINEL_FLOAT: float = float('-inf')  # Para campos float / double
SENTINEL_STR: str = ''                 # Para campos string

class HeapFile:
    """Almacenamiento en heap (archivo secuencial) con soporte
    opcional de clave primaria única.
    
    Se garantiza la unicidad de la clave primaria *solo* mediante
    búsqueda lineal.  Para un rendimiento O(log n) deberá usarse
    posteriormente un índice externo (B+‑Tree, hash, etc.).
    """

    METADATA_FORMAT = "i"      # almacena heap_size al inicio del archivo
    METADATA_SIZE = struct.calcsize(METADATA_FORMAT)

    # ------------------------------------------------------------------
    # Creación del archivo ------------------------------------------------
    # ------------------------------------------------------------------
    @staticmethod
    def build_file(table_name: str,
                   schema: List[Tuple[str, str]],
                   primary_key: Optional[str] = None) -> None:
        """Crea un nuevo archivo heap vacío y su archivo de esquema JSON.

        Args:
            table_name: nombre lógico de la tabla (sin extensión).
            schema: lista (name, fmt) estilo struct.
            primary_key: nombre del campo que actuará como PK o None.
        """
        # 1) Archivo binario
        filename = table_name + ".dat"
        with open(filename, "wb") as f:
            metadata = struct.pack(HeapFile.METADATA_FORMAT, 0)  # heap_size = 0
            f.write(metadata)

        # 2) Archivo de esquema JSON
        schema_file = table_name + ".schema.json"
        fields = [
            {
                "name": name,
                "type": fmt,
                "is_primary_key": (name == primary_key)
            }
            for name, fmt in schema
        ]
        schema_json = {
            "table_name": os.path.splitext(os.path.basename(table_name))[0],
            "fields": fields
        }
        with open(schema_file, "w", encoding="utf‑8") as f:
            json.dump(schema_json, f, indent=4)

    # ------------------------------------------------------------------
    # Inicialización -----------------------------------------------------
    # ------------------------------------------------------------------
    def __init__(self, table_name: str) -> None:
        self.filename = table_name + ".dat"
        self.schema, self.primary_key = self._load_schema(self.filename)
        self.record_size = Record.get_size(self.schema)

        if not os.path.exists(self.filename):
            raise FileNotFoundError(
                f"El archivo {self.filename} no existe. Crea la tabla primero.")

        with open(self.filename, "rb") as f:
            meta_buf = f.read(self.METADATA_SIZE)
            self.heap_size = struct.unpack(self.METADATA_FORMAT, meta_buf)[0]

    # ------------------------------------------------------------------
    # Utilidades internas ------------------------------------------------
    # ------------------------------------------------------------------
    def _load_schema(self, filename: str) -> Tuple[List[Tuple[str, str]], Optional[str]]:
        """Devuelve (schema, primary_key_name) leídos de <tabla>.schema.json."""
        schema_file = filename.replace(".dat", ".schema.json")
        with open(schema_file, "r", encoding="utf‑8") as f:
            schema_json = json.load(f)
        schema: List[Tuple[str, str]] = [
            (fld["name"], fld["type"]) for fld in schema_json["fields"]
        ]
        pk = next((fld["name"] for fld in schema_json["fields"]
                   if fld.get("is_primary_key")), None)
        return schema, pk

    def _pk_index_and_format(self) -> Tuple[int, str]:
        if self.primary_key is None:
            raise ValueError("La tabla no tiene clave primaria definida.")
        for idx, (name, fmt) in enumerate(self.schema):
            if name == self.primary_key:
                return idx, fmt
        raise RuntimeError("Clave primaria no encontrada en schema (inconsistente).")

    @staticmethod
    def _sentinel_for_format(fmt: str):
        if any(c in fmt for c in ("i", "q")):
            return SENTINEL_INT
        if any(c in fmt for c in ("f", "d")):
            return SENTINEL_FLOAT
        if "s" in fmt:
            return SENTINEL_STR
        raise ValueError(f"Formato no soportado en sentinel: {fmt}")

    # ------------------------------------------------------------------
    # Metadata -----------------------------------------------------------
    # ------------------------------------------------------------------
    def _update_heap_size(self, fh):
        fh.seek(0)
        fh.write(struct.pack(self.METADATA_FORMAT, self.heap_size))

    # ------------------------------------------------------------------
    # Inserción ----------------------------------------------------------
    # ------------------------------------------------------------------
    def insert_record(self, record: Record) -> int:
        """Inserta un registro al final verificando unicidad de la PK.

        Retorna el número lógico del registro (offset)."""
        # 1) Validar esquema
        if record.schema != self.schema:
            raise ValueError("El esquema del registro no coincide con el archivo.")

        # 2) Validar clave primaria (si existe)
        if self.primary_key:
            pk_idx, pk_fmt = self._pk_index_and_format()
            pk_val = record.values[pk_idx]
            sentinel = self._sentinel_for_format(pk_fmt)

            if pk_val == sentinel:
                raise ValueError("El valor de la clave primaria no puede ser el centinela de borrado.")

            # Búsqueda lineal O(n)
            for i in range(self.heap_size):
                existing = self.fetch_record_by_offset(i)
                existing_pk = existing.values[pk_idx]
                if existing_pk == pk_val:
                    raise ValueError(f"Clave primaria duplicada: {pk_val}")

        # 3) Escribir al final y actualizar metadata
        with open(self.filename, "r+b") as fh:
            fh.seek(0, os.SEEK_END)
            fh.write(record.pack())
            self.heap_size += 1
            self._update_heap_size(fh)
            return self.heap_size - 1

    # ------------------------------------------------------------------
    # Búsqueda por clave primaria ---------------------------------------
    # ------------------------------------------------------------------
    def search_by_pk(self, key) -> Optional[Record]:
        """Devuelve el registro cuya clave primaria == key, o None."""
        if self.primary_key is None:
            raise ValueError("La tabla no define clave primaria.")
        pk_idx, _ = self._pk_index_and_format()
        with open(self.filename, "rb") as fh:
            fh.seek(self.METADATA_SIZE)
            for _ in range(self.heap_size):
                buf = fh.read(self.record_size)
                if len(buf) < self.record_size:
                    break
                rec = Record.unpack(buf, self.schema)
                if rec.values[pk_idx] == key:
                    return rec
        return None

    # ------------------------------------------------------------------
    # Extracción de índice ------------------------------------------------
    # ------------------------------------------------------------------
    def extract_index(self, key_field: str) -> List[Tuple[object, int]]:
        """Devuelve [(valor, rec_num)] para *key_field* ignorando borrados."""
        field_names = [n for n, _ in self.schema]
        if key_field not in field_names:
            raise KeyError(f"Campo '{key_field}' no existe en el esquema")
        key_pos = field_names.index(key_field)

        deleted_sentinel = None
        if key_field == self.primary_key:
            _, fmt = self._pk_index_and_format()
            deleted_sentinel = self._sentinel_for_format(fmt)

        entries = []
        with open(self.filename, "rb") as fh:
            fh.seek(self.METADATA_SIZE)
            rec_num = 0
            while True:
                buf = fh.read(self.record_size)
                if len(buf) < self.record_size:
                    break
                rec = Record.unpack(buf, self.schema)
                key_val = rec.values[key_pos]
                if deleted_sentinel is not None and key_val == deleted_sentinel:
                    rec_num += 1
                    continue  # registro eliminado
                entries.append((key_val, rec_num))
                rec_num += 1
        return entries

    # ------------------------------------------------------------------
    # Acceso directo por offset -----------------------------------------
    # ------------------------------------------------------------------
    def fetch_record_by_offset(self, rec_num: int) -> Record:
        if rec_num < 0 or rec_num >= self.heap_size:
            raise IndexError(f"Offset {rec_num} fuera de rango (0..{self.heap_size - 1})")
        with open(self.filename, "rb") as fh:
            byte_off = self.METADATA_SIZE + rec_num * self.record_size
            fh.seek(byte_off)
            buf = fh.read(self.record_size)
            return Record.unpack(buf, self.schema)

    # ------------------------------------------------------------------
    # Impresión utilitaria ----------------------------------------------
    # ------------------------------------------------------------------
    def print_all(self) -> None:
        print(f"Metadata (heap_size): {self.heap_size}")
        headers = [n for n, _ in self.schema]
        print(" | ".join(headers))
        print("-" * (len(headers) * 10))
        with open(self.filename, "rb") as fh:
            fh.seek(self.METADATA_SIZE)
            for _ in range(self.heap_size):
                buf = fh.read(self.record_size)
                rec = Record.unpack(buf, self.schema)
                rec.print()
