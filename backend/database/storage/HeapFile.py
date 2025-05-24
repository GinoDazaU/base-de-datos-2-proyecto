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

# --------------------------------------------------------
#  Constantes internas
# --------------------------------------------------------
PTR_SIZE = 4                              # int32 para enlazar free‑list
METADATA_FORMAT = "ii"                  # [heap_size, free_head]
METADATA_SIZE   = struct.calcsize(METADATA_FORMAT)

class HeapFile:
    """Archivo heap con clave primaria opcional y free‑list interna.

    • Cada *slot* = datos de Record + 4 bytes (next_free).
    • Cuando un slot está libre: PK = centinela y next_free apunta al
      siguiente hueco (o -1 si es el último).
    • Offsets lógicos nunca cambian, así los índices externos se mantienen.
    """

    # ------------------------------------------------------------------
    # Creación del archivo ---------------------------------------------
    # ------------------------------------------------------------------
    @staticmethod
    def build_file(table_name: str,
                   schema: List[Tuple[str, str]],
                   primary_key: Optional[str] = None) -> None:
        """Crea archivo <table_name>.dat y <table_name>.schema.json."""
        filename = table_name + ".dat"
        with open(filename, "wb") as f:
            f.write(struct.pack(METADATA_FORMAT, 0, -1))   # heap_size=0, free_head=-1

        schema_file = table_name + ".schema.json"
        fields = [
            {"name": n, "type": fmt, "is_primary_key": (n == primary_key)}
            for n, fmt in schema
        ]
        with open(schema_file, "w", encoding="utf-8") as jf:
            json.dump({"table_name": os.path.basename(table_name), "fields": fields},
                      jf, indent=4)

    # ------------------------------------------------------------------
    # Inicialización ----------------------------------------------------
    # ------------------------------------------------------------------
    def __init__(self, table_name: str):
        self.filename = table_name + ".dat"
        self.schema, self.primary_key = self._load_schema(self.filename)
        self.rec_data_size = Record.get_size(self.schema)
        self.slot_size     = self.rec_data_size + PTR_SIZE

        if not os.path.exists(self.filename):
            raise FileNotFoundError(f"{self.filename} no existe. Cree la tabla primero.")

        with open(self.filename, "rb") as f:
            self.heap_size, self.free_head = struct.unpack(METADATA_FORMAT,
                                                           f.read(METADATA_SIZE))

    # ------------------------------------------------------------------
    # Utilidades internas ----------------------------------------------
    # ------------------------------------------------------------------
    def _load_schema(self, fname) -> Tuple[List[Tuple[str, str]], Optional[str]]:
        with open(fname.replace(".dat", ".schema.json"), encoding="utf-8") as jf:
            js = json.load(jf)
        schema = [(fld["name"], fld["type"]) for fld in js["fields"]]
        pk = next((fld["name"] for fld in js["fields"] if fld.get("is_primary_key")), None)
        return schema, pk

    def _pk_idx_fmt(self) -> Tuple[int, str]:
        if self.primary_key is None:
            raise ValueError("La tabla no tiene clave primaria definida.")
        for i, (n, fmt) in enumerate(self.schema):
            if n == self.primary_key:
                return i, fmt
        raise RuntimeError("Inconsistencia en schema: PK no encontrada.")

    @staticmethod
    def _sentinel(fmt: str):
        if "s" in fmt:
            return SENTINEL_STR
        if fmt[-1] in "fd":
            return SENTINEL_FLOAT
        return SENTINEL_INT

    def _write_header(self, fh):
        fh.seek(0)
        fh.write(struct.pack(METADATA_FORMAT, self.heap_size, self.free_head))

    # ------------------------------------------------------------------
    # Inserción ---------------------------------------------------------
    # ------------------------------------------------------------------
    def insert_record(self, record: Record) -> int:
        if record.schema != self.schema:
            raise ValueError("Esquema del registro no coincide.")

        # ── 1. Verificar unicidad de PK en una SOLA pasada ─────────────
        if self.primary_key:
            pk_idx, pk_fmt = self._pk_idx_fmt()
            pk_val = record.values[pk_idx]
            if pk_val == self._sentinel(pk_fmt):
                raise ValueError("Valor centinela no permitido en PK.")

            with open(self.filename, "rb") as fh:      # una sola apertura
                fh.seek(METADATA_SIZE)
                for _ in range(self.heap_size):
                    buf = fh.read(self.rec_data_size)
                    if len(buf) < self.rec_data_size:
                        break
                    if Record.unpack(buf, self.schema).values[pk_idx] == pk_val:
                        raise ValueError(f"PK duplicada: {pk_val}")
                    fh.seek(PTR_SIZE, os.SEEK_CUR)     # saltar next_free

        # ── 2. Insertar (reciclar hueco o append) ─────────────────────
        with open(self.filename, "r+b") as fh:
            if self.free_head == -1:                    # sin huecos → append
                slot_off = self.heap_size
                fh.seek(0, os.SEEK_END)
                fh.write(record.pack())
                fh.write(struct.pack("i", 0))           # next_free = 0
                self.heap_size += 1
            else:                                      # reciclar hueco
                slot_off = self.free_head
                byte_off = METADATA_SIZE + slot_off * self.slot_size
                fh.seek(byte_off + self.rec_data_size)
                self.free_head = struct.unpack("i", fh.read(4))[0]  # siguiente libre
                fh.seek(byte_off)
                fh.write(record.pack())
                fh.write(struct.pack("i", 0))
            self._write_header(fh)                      # actualizar cabecera
            return slot_off
    # ------------------------------------------------------------------
    # Borrado -----------------------------------------------------------
    # ------------------------------------------------------------------
    def delete_by_pk(self, key) -> Tuple[bool, int, Optional[Record]]:
        if self.primary_key is None:
            raise ValueError("Tabla sin clave primaria.")
        pk_idx, pk_fmt = self._pk_idx_fmt()
        sentinel = self._sentinel(pk_fmt)

        with open(self.filename, "r+b") as fh:
            for pos in range(self.heap_size):
                byte_off = METADATA_SIZE + pos * self.slot_size
                fh.seek(byte_off)
                buf = fh.read(self.rec_data_size)
                rec = Record.unpack(buf, self.schema)
                if rec.values[pk_idx] != key:
                    continue
                # marcar hueco: set PK = sentinel y next_free = free_head
                rec.values[pk_idx] = sentinel
                fh.seek(byte_off)
                fh.write(rec.pack())
                fh.write(struct.pack("i", self.free_head))
                self.free_head = pos
                self._write_header(fh)
                return True, pos, rec
        return False, -1, None

    # ------------------------------------------------------------------
    # Extracción de índice (ignora huecos) -----------------------------
    # ------------------------------------------------------------------
    def extract_index(self, field):
        names = [n for n, _ in self.schema]
        if field not in names:
            raise KeyError(f"Campo '{field}' no existe.")
        fld_idx = names.index(field)

        pk_idx, pk_sentinel = None, None
        if self.primary_key is not None:
            pk_idx, pk_fmt = self._pk_idx_fmt()
            pk_sentinel = self._sentinel(pk_fmt)

        out, pos = [], 0
        with open(self.filename, "rb") as fh:
            fh.seek(METADATA_SIZE)
            while pos < self.heap_size:
                buf = fh.read(self.rec_data_size)
                if len(buf) < self.rec_data_size:
                    break
                rec = Record.unpack(buf, self.schema)
                # saltar huecos
                if pk_idx is not None and rec.values[pk_idx] == pk_sentinel:
                    fh.seek(PTR_SIZE, os.SEEK_CUR)
                    pos += 1
                    continue
                out.append((rec.values[fld_idx], pos))
                fh.seek(PTR_SIZE, os.SEEK_CUR)
                pos += 1
        return out

    # ------------------------------------------------------------------
    # Fetch por offset --------------------------------------------------
    # ------------------------------------------------------------------
    def fetch_record_by_offset(self, pos: int) -> Record:
        if pos < 0 or pos >= self.heap_size:
            raise IndexError("Offset fuera de rango")
        with open(self.filename, "rb") as fh:
            fh.seek(METADATA_SIZE + pos * self.slot_size)
            buf = fh.read(self.rec_data_size)
            return Record.unpack(buf, self.schema)

    # ------------------------------------------------------------------
    # Utilidades de depuración -----------------------------------------
    # ------------------------------------------------------------------
    def print_all(self):
        print(f"heap_size={self.heap_size}, free_head={self.free_head}")
        names = [n for n, _ in self.schema]
        print(" | ".join(names))
        print("-" * 10 * len(names))
        with open(self.filename, "rb") as fh:
            fh.seek(METADATA_SIZE)
            for i in range(self.heap_size):
                buf = fh.read(self.rec_data_size)
                rec = Record.unpack(buf, self.schema)
                rec.print()
                fh.seek(PTR_SIZE, os.SEEK_CUR)
