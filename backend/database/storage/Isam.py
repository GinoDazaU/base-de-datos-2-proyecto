import os
import json
import struct
from bisect import bisect_right
from typing import List, Tuple, Union, Optional

# ---------------------------------------------------------------------------
#  CONFIGURACIÓN GLOBAL
# ---------------------------------------------------------------------------
BLOCK_SIZE      = 4096            # tamaño de página fijo
SENTINEL_INT    = -1              # clave vacía (enteros)
SENTINEL_FLOAT  = -float('inf')   # clave vacía (floats)  
SENTINEL_STR    = ''              # clave vacía (cadenas)

# ---------------------------------------------------------------------------
#  INDEX RECORD – sin cambios
# ---------------------------------------------------------------------------
class IndexRecord:
    TYPE_INT    = 0
    TYPE_FLOAT  = 1
    TYPE_STRING = 2

    def __init__(self, fmt: str, key: Union[int, float, str], offset: int):
        self.fmt    = fmt
        self.key    = key
        self.offset = offset
        self._validate()

    # ---------- validación --------------------------------------------------
    def _validate(self):
        if self.fmt == 'i' and not isinstance(self.key, int):
            raise TypeError("Clave debe ser int para formato 'i'")
        if self.fmt == 'f' and not isinstance(self.key, float):
            raise TypeError("Clave debe ser float para formato 'f'")
        if 's' in self.fmt and not isinstance(self.key, str):
            raise TypeError("Clave debe ser str para formato 'Ns'")

    # ---------- serialización ----------------------------------------------
    def pack(self) -> bytes:
        if self.fmt == 'i':
            return struct.pack('Bii', self.TYPE_INT,   self.key, self.offset)
        if self.fmt == 'f':
            return struct.pack('Bfi', self.TYPE_FLOAT, self.key, self.offset)
        size    = int(self.fmt[:-1])
        encoded = self.key.encode()[:size].ljust(size, b'\x00')
        return struct.pack(f'B{size}si', self.TYPE_STRING, encoded, self.offset)

    @staticmethod
    def unpack(buf: bytes, fmt: str) -> 'IndexRecord':
        tag = buf[0]
        if tag == IndexRecord.TYPE_INT:
            _, k, off = struct.unpack_from('Bii', buf)
            return IndexRecord('i', k, off)
        if tag == IndexRecord.TYPE_FLOAT:
            _, k, off = struct.unpack_from('Bfi', buf)
            return IndexRecord('f', k, off)
        size      = int(fmt[:-1])
        _, enc, off = struct.unpack_from(f'B{size}si', buf)
        return IndexRecord(fmt, enc.rstrip(b'\x00').decode(), off)

    # ---------- utilidades --------------------------------------------------
    @property
    def size(self) -> int:
        if self.fmt == 'i': return struct.calcsize('Bii')
        if self.fmt == 'f': return struct.calcsize('Bfi')
        size = int(self.fmt[:-1])
        return struct.calcsize(f'B{size}si')

    def __lt__(self, other):
        return self.key < other.key

    def __repr__(self):
        return f"IndexRecord({self.key!r}, off={self.offset})"

# ---------------------------------------------------------------------------
#  RECORD – sin cambios
# ---------------------------------------------------------------------------
class Record:
    def __init__(self, schema: List[Tuple[str, str]], values: List[Union[int, float, str]]):
        self.schema = schema
        self.values = values
        self.fmt    = ''.join(fmt for _, fmt in schema)
        self.size   = struct.calcsize(self.fmt)

    # ---------- serialización ----------------------------------------------
    def pack(self) -> bytes:
        processed = []
        for (_, fmt), val in zip(self.schema, self.values):
            if 's' in fmt:
                size = int(fmt[:-1])
                val  = val.encode()[:size].ljust(size, b'\x00')
            processed.append(val)
        return struct.pack(self.fmt, *processed)

    @staticmethod
    def unpack(buf: bytes, schema):
        fmt   = ''.join(f for _, f in schema)
        vals  = list(struct.unpack(fmt, buf))
        clean = []
        for (_, f), v in zip(schema, vals):
            if 's' in f:
                v = v.rstrip(b'\x00').decode()
            clean.append(v)
        return Record(schema, clean)

    @staticmethod
    def get_size(schema):
        return struct.calcsize(''.join(f for _, f in schema))

    def __repr__(self):
        return f"Record({self.values})"

# ---------------------------------------------------------------------------
#  FUNCIONES AUXILIARES
# ---------------------------------------------------------------------------

def get_sentinel(fmt: str):
    if fmt == 'i':  return SENTINEL_INT
    if fmt == 'f':  return SENTINEL_FLOAT
    return SENTINEL_STR


def dummy_key(fmt: str):
    if fmt == 'i':  return 0
    if fmt == 'f':  return 0.0
    return ''


def create_empty_record(schema, key_idx):
    vals = []
    for i, (_, fmt) in enumerate(schema):
        if i == key_idx:
            vals.append(get_sentinel(fmt))
        elif fmt == 'i':
            vals.append(0)
        elif fmt == 'f':
            vals.append(0.0)
        else:
            size = int(fmt[:-1])
            vals.append('\x00' * size)
    return Record(schema, vals)

# ---------------------------------------------------------------------------
#  CLASE ISAM
# ---------------------------------------------------------------------------
class ISAM:
    def __init__(self, table: str):
        self.table = table
        self._load_meta()

    # ---------------- CONSTRUCCIÓN INICIAL ---------------------------------
    @staticmethod
    def build_isam(table: str, schema, key_field: str):
        key_idx = next(i for i,(n,_) in enumerate(schema) if n == key_field)
        key_fmt = schema[key_idx][1]

        rec_size       = Record.get_size(schema)
        recs_per_pg    = BLOCK_SIZE // rec_size
        idx_rec_size   = IndexRecord(key_fmt, dummy_key(key_fmt), 0).size  # ← fix
        idx_per_pg     = BLOCK_SIZE // idx_rec_size

        # ---- datos vacíos --------------------------------------------------
        empty_page = create_empty_record(schema, key_idx).pack() * recs_per_pg
        with open(f"{table}.isam.dat", 'wb') as f:
            f.write(empty_page)

        # ---- segundo nivel -------------------------------------------------
        leaf_entry = IndexRecord(key_fmt, get_sentinel(key_fmt), 0).pack()
        with open(f"{table}.isam2.idx", 'wb') as f:
            f.write(leaf_entry * idx_per_pg)

        # ---- primer nivel --------------------------------------------------
        root_entry = IndexRecord(key_fmt, get_sentinel(key_fmt), 0).pack()
        with open(f"{table}.isam1.idx", 'wb') as f:
            f.write(root_entry * idx_per_pg)

        # ---- overflow vacío ------------------------------------------------
        open(f"{table}.isam.overflow.dat", 'wb').close()

        meta = {
            "schema": schema,
            "key_field": key_field,
            "block_size": BLOCK_SIZE,
            "record_size": rec_size,
            "records_per_page": recs_per_pg,
            "index_record_size": idx_rec_size,
            "index_entries_per_page": idx_per_pg,
            "key_format": key_fmt
        }
        with open(f"{table}.isam.meta.json", 'w', encoding='utf-8') as fm:
            json.dump(meta, fm, indent=2)

    # ---------------- BÚSQUEDA ---------------------------------------------
    def search(self, key) -> Optional[Record]:
        root = self._seek_index(f"{self.table}.isam1.idx", key)
        leaf = self._seek_index(f"{self.table}.isam2.idx", key, base_off=root.offset)
        data_off = leaf.offset
        # leer página de datos
        with open(f"{self.table}.isam.dat", 'rb') as fd:
            fd.seek(data_off)
            page = fd.read(BLOCK_SIZE)
        rec = self._linear_scan(page, key)
        if rec: return rec
        return self._scan_overflow(key)

    # ---------------- INSERCIÓN --------------------------------------------
    def insert(self, record: Record):
        key_idx = next(i for i,(n,_) in enumerate(self.meta['schema']) if n==self.meta['key_field'])
        key     = record.values[key_idx]

        root = self._seek_index(f"{self.table}.isam1.idx", key)
        leaf = self._seek_index(f"{self.table}.isam2.idx", key, base_off=root.offset)
        data_off = leaf.offset

        rec_sz  = self.meta['record_size']
        per_pg  = self.meta['records_per_page']
        page_modified = False

        with open(f"{self.table}.isam.dat", 'r+b') as fd:
            fd.seek(data_off)
            page = bytearray(fd.read(BLOCK_SIZE))
            keys = []
            for i in range(per_pg):
                buf = page[i*rec_sz:(i+1)*rec_sz]
                r   = Record.unpack(buf, self.meta['schema'])
                keys.append(r.values[key_idx])
            try:
                first_empty = keys.index(get_sentinel(self.meta['key_format']))
            except ValueError:  # página llena
                with open(f"{self.table}.isam.overflow.dat", 'ab') as fo:
                    fo.write(record.pack())
                return
            insert_pos = bisect_right(keys, key, hi=first_empty)
            # shift
            for i in range(first_empty, insert_pos, -1):
                dst = i*rec_sz
                src = (i-1)*rec_sz
                page[dst:dst+rec_sz] = page[src:src+rec_sz]
            page[insert_pos*rec_sz:(insert_pos+1)*rec_sz] = record.pack()
            page_modified = True

            if page_modified:
                fd.seek(data_off)
                fd.write(page)

    # ---------------- UTILITARIOS PRIVADOS ---------------------------------
    def _load_meta(self):
        with open(f"{self.table}.isam.meta.json", 'r', encoding='utf-8') as fm:
            self.meta = json.load(fm)

    def _seek_index(self, idx_file: str, key, base_off: int = 0) -> IndexRecord:
        ent_sz  = self.meta['index_record_size']
        per_pg  = self.meta['index_entries_per_page']
        fmt     = self.meta['key_format']
        with open(idx_file, 'rb') as fi:
            fi.seek(base_off)
            page = fi.read(BLOCK_SIZE)
        entries, keys = [], []
        for i in range(per_pg):
            buf = page[i*ent_sz:(i+1)*ent_sz]
            rec = IndexRecord.unpack(buf, fmt)
            entries.append(rec)
            keys.append(rec.key)
        idx = max(bisect_right(keys, key) - 1, 0)
        return entries[idx]

    def _linear_scan(self, page: bytes, key):
        rec_sz = self.meta['record_size']
        schema = self.meta['schema']
        key_idx = next(i for i,(n,_) in enumerate(schema) if n==self.meta['key_field'])
        for i in range(self.meta['records_per_page']):
            buf = page[i*rec_sz:(i+1)*rec_sz]
            r   = Record.unpack(buf, schema)
            if r.values[key_idx] == key:
                return r
        return None

    def _scan_overflow(self, key):
        rec_sz = self.meta['record_size']
        schema = self.meta['schema']
        key_idx = next(i for i,(n,_) in enumerate(schema) if n==self.meta['key_field'])
        with open(f"{self.table}.isam.overflow.dat", 'rb') as fo:
            while True:
                buf = fo.read(rec_sz)
                if not buf:
                    break
                r = Record.unpack(buf, schema)
                if r.values[key_idx] == key:
                    return r
        return None
    
    def print_all(self):
        print("\n📁 ISAM – INDICE DE PRIMER NIVEL (.isam1.idx):")
        self._print_index(f"{self.table}.isam1.idx")

        print("\n📁 ISAM – INDICE DE SEGUNDO NIVEL (.isam2.idx):")
        self._print_index(f"{self.table}.isam2.idx")

        print("\n📁 ISAM – DATOS PRINCIPALES (.isam.dat):")
        self._print_data_pages()

        print("\n📁 ISAM – OVERFLOW (.isam.overflow.dat):")
        self._print_overflow()

    def _print_index(self, filepath):
        ent_sz = self.meta['index_record_size']
        fmt = self.meta['key_format']
        with open(filepath, 'rb') as f:
            page_num = 0
            while True:
                page = f.read(BLOCK_SIZE)
                if not page:
                    break
                print(f"\nPágina de índice #{page_num}:")
                for i in range(self.meta['index_entries_per_page']):
                    buf = page[i*ent_sz:(i+1)*ent_sz]
                    rec = IndexRecord.unpack(buf, fmt)
                    print(f"  {i}: {rec}")
                page_num += 1

    def _print_data_pages(self):
        rec_sz = self.meta['record_size']
        schema = self.meta['schema']
        with open(f"{self.table}.isam.dat", 'rb') as f:
            page_num = 0
            while True:
                page = f.read(BLOCK_SIZE)
                if not page:
                    break
                print(f"\nPágina de datos #{page_num}:")
                for i in range(self.meta['records_per_page']):
                    buf = page[i*rec_sz:(i+1)*rec_sz]
                    rec = Record.unpack(buf, schema)
                    print(f"  {i}: {rec}")
                page_num += 1

    def _print_overflow(self):
        rec_sz = self.meta['record_size']
        schema = self.meta['schema']
        with open(f"{self.table}.isam.overflow.dat", 'rb') as f:
            i = 0
            while True:
                buf = f.read(rec_sz)
                if not buf:
                    break
                rec = Record.unpack(buf, schema)
                print(f"  {i}: {rec}")
                i += 1



if __name__ == '__main__':
    from faker import Faker
    import os

    fake = Faker()
    table_name = "test_isam"
    schema = [("nombre", "10s"), ("precio", "f"), ("cantidad", "i")]

    # Eliminar archivos previos
    for ext in [".isam.dat", ".isam1.idx", ".isam2.idx", ".isam.overflow.dat", ".isam.meta.json"]:
        try:
            os.remove(f"{table_name}{ext}")
        except FileNotFoundError:
            pass

    # Crear estructura ISAM
    ISAM.build_isam(table_name, schema, "nombre")
    idx = ISAM(table_name)

    # Insertar 500 registros aleatorios para llegar al overflow
    print("Insertando registros con faker...")
    for i in range(1000):
        nombre = fake.first_name()[:10]  # limitar a 10 caracteres
        precio = round(fake.random_number(digits=2) + fake.random.random(), 2)
        cantidad = fake.random_int(min=1, max=100)
        idx.insert(Record(schema, [nombre, precio, cantidad]))
        if i % 100 == 0:
            print(f"{i} registros insertados...")

    # Buscar algunos registros aleatorios para comprobar que se insertaron correctamente
    print("\nBuscando 10 registros aleatorios:")
    for _ in range(10):
        nombre = fake.first_name()[:10]
        resultado = idx.search(nombre)
        print(f"Buscar '{nombre}': {'✅ Encontrado' if resultado else '🆗 No encontrado'}")

    print("\n✅ Test finalizado: se insertaron 500 registros aleatorios.")

    idx.print_all()