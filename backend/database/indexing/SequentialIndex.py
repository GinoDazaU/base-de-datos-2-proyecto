import struct
import math
import os

from .IndexRecord import IndexRecord

class SequentialIndex:
    METADATA_FORMAT = "iii"
    METADATA_SIZE = struct.calcsize(METADATA_FORMAT)

    def __init__(self, filename: str):
        # Inicializa el índice secuencial leyendo los metadatos.
        self.filename = filename

        if not os.path.exists(filename):
            raise FileNotFoundError(f"El índice para {filename} no existe. Crea el índice primero.")

        with open(self.filename, "rb+") as f:
            meta = f.read(self.METADATA_SIZE)
            self.main_size, self.aux_size, self.max_aux_size = struct.unpack(self.METADATA_FORMAT, meta)

    @staticmethod
    def build_index(heap_filename: str, extract_index_fn, key_field: str = "id"):
        """
        Construye el índice desde cero a partir de un heapfile dado su nombre.
        `extract_index_fn(key_field)` debe devolver una lista de tuplas (key, offset).
        Genera automáticamente el nombre `{base}.seq.idx`.
        """
        base, _ = os.path.splitext(heap_filename)
        idx_filename = f"{base}.{key_field}.seq.idx"

        entries = extract_index_fn(key_field)
        entries.sort(key=lambda x: x[0])

        main_size = len(entries)
        aux_size = 0
        max_aux_size = max(1, math.floor(math.log2(main_size))) if main_size > 0 else 1

        with open(idx_filename, "wb") as f:
            f.write(struct.pack(SequentialIndex.METADATA_FORMAT, main_size, aux_size, max_aux_size))
            for key, offset in entries:
                rec = IndexRecord(key, offset)
                f.write(rec.pack())
            empty = IndexRecord(-1, 0).pack()
            for _ in range(max_aux_size):
                f.write(empty)

        return SequentialIndex(idx_filename)

    def update_metadata(self, file_handle=None):
        """
        Actualiza los metadatos en disco. Si se pasa un file_handle abierto, lo utiliza, sino abre el archivo.
        """
        if file_handle:
            file_handle.seek(0)
            file_handle.write(struct.pack(self.METADATA_FORMAT, self.main_size, self.aux_size, self.max_aux_size))
        else:
            with open(self.filename, "r+b") as f:
                f.seek(0)
                f.write(struct.pack(self.METADATA_FORMAT, self.main_size, self.aux_size, self.max_aux_size))

    def insert_record(self, record: IndexRecord):
        """
        Inserta un IndexRecord en el área auxiliar. Si se supera el tamaño máximo permitido para auxiliar,
        se reconstruye el archivo fusionando principal y auxiliar.
        """
        with open(self.filename, "r+b") as f:
            f.seek(self.METADATA_SIZE + self.main_size * IndexRecord.SIZE + self.aux_size * IndexRecord.SIZE)
            f.write(record.pack())
            self.aux_size += 1
            self.update_metadata(file_handle=f)

        if self.aux_size > self.max_aux_size:
            self.rebuild_file()

    def rebuild_file(self):
        """
        Fusiona las zonas principal y auxiliar, elimina los eliminados lógicamente, ordena por clave
        y reescribe el archivo de índice completo con metadatos actualizados.
        """
        all_recs: list[IndexRecord] = []
        with open(self.filename, "rb") as f:
            f.seek(self.METADATA_SIZE)
            for _ in range(self.main_size):
                buf = f.read(IndexRecord.SIZE)
                if not buf:
                    break
                r = IndexRecord.unpack(buf)
                if r.key != -1:
                    all_recs.append(r)
            f.seek(self.METADATA_SIZE + self.main_size * IndexRecord.SIZE)
            for _ in range(self.aux_size):
                buf = f.read(IndexRecord.SIZE)
                if not buf:
                    break
                r = IndexRecord.unpack(buf)
                if r.key != -1:
                    all_recs.append(r)

        all_recs.sort(key=lambda r: r.key)
        new_main = len(all_recs)
        new_aux_max = max(1, math.floor(math.log2(new_main))) if new_main > 0 else 1

        tmp = self.filename + ".tmp"
        with open(tmp, "wb") as f:
            f.write(struct.pack(self.METADATA_FORMAT, new_main, 0, new_aux_max))
            for r in all_recs:
                f.write(r.pack())
            empty = IndexRecord(-1, 0).pack()
            for _ in range(new_aux_max):
                f.write(empty)

        os.replace(tmp, self.filename)
        self.main_size = new_main
        self.aux_size = 0
        self.max_aux_size = new_aux_max

    def search_record(self, key: int) -> IndexRecord | None:
        """
        Busca un IndexRecord por clave. Utiliza búsqueda binaria en la zona principal
        y búsqueda secuencial en la zona auxiliar.
        """
        with open(self.filename, "rb") as f:
            f.seek(self.METADATA_SIZE)
            left, right = 0, self.main_size - 1
            while left <= right:
                mid = (left + right) // 2
                f.seek(self.METADATA_SIZE + mid * IndexRecord.SIZE)
                rec = IndexRecord.unpack(f.read(IndexRecord.SIZE))
                if rec.key == key:
                    return rec
                if rec.key < key:
                    left = mid + 1
                else:
                    right = mid - 1

            f.seek(self.METADATA_SIZE + self.main_size * IndexRecord.SIZE)
            for _ in range(self.aux_size):
                rec = IndexRecord.unpack(f.read(IndexRecord.SIZE))
                if rec.key == key:
                    return rec

        return None

    def delete_record(self, key: int) -> bool:
        """
        Realiza un borrado lógico (key = -1) en la zona principal o auxiliar. 
        Devuelve True si se encuentra y elimina, False en caso contrario.
        """
        with open(self.filename, "r+b") as f:
            f.seek(self.METADATA_SIZE)
            left, right = 0, self.main_size - 1
            while left <= right:
                mid = (left + right) // 2
                f.seek(self.METADATA_SIZE + mid * IndexRecord.SIZE)
                rec = IndexRecord.unpack(f.read(IndexRecord.SIZE))
                if rec.key == key:
                    f.seek(-IndexRecord.SIZE, os.SEEK_CUR)
                    f.write(IndexRecord(-1, 0).pack())
                    return True
                if rec.key < key:
                    left = mid + 1
                else:
                    right = mid - 1

            f.seek(self.METADATA_SIZE + self.main_size * IndexRecord.SIZE)
            for _ in range(self.aux_size):
                pos = f.tell()
                rec = IndexRecord.unpack(f.read(IndexRecord.SIZE))
                if rec.key == key:
                    f.seek(pos)
                    f.write(IndexRecord(-1, 0).pack())
                    self.aux_size -= 1
                    self.update_metadata(file_handle=f)
                    return True

        return False

    def search_range(self, start_key: int, end_key: int) -> list[IndexRecord]:
        """
        Devuelve todos los registros cuya clave esté dentro del rango [start_key, end_key].
        La zona principal se recorre desde el primer índice válido.
        La zona auxiliar se recorre completamente.
        """
        results: list[IndexRecord] = []
        with open(self.filename, "rb") as f:
            f.seek(self.METADATA_SIZE)
            left, right = 0, self.main_size - 1
            pos0 = 0
            while left <= right:
                mid = (left + right) // 2
                f.seek(self.METADATA_SIZE + mid * IndexRecord.SIZE)
                rec = IndexRecord.unpack(f.read(IndexRecord.SIZE))
                if rec.key < start_key:
                    left = mid + 1
                else:
                    right = mid - 1
                    pos0 = mid
            f.seek(self.METADATA_SIZE + pos0 * IndexRecord.SIZE)
            for _ in range(pos0, self.main_size):
                rec = IndexRecord.unpack(f.read(IndexRecord.SIZE))
                if rec.key > end_key:
                    break
                if rec.key != -1:
                    results.append(rec)

            f.seek(self.METADATA_SIZE + self.main_size * IndexRecord.SIZE)
            for _ in range(self.aux_size):
                rec = IndexRecord.unpack(f.read(IndexRecord.SIZE))
                if start_key <= rec.key <= end_key:
                    results.append(rec)

        return results

    def print_all(self):
        """
        Imprime los metadatos y todos los registros, diferenciando entre zona principal y auxiliar.
        """
        with open(self.filename, "rb") as f:
            meta = f.read(self.METADATA_SIZE)
            ms, au, ma = struct.unpack(self.METADATA_FORMAT, meta)
            print(f"Main: {ms}, Aux: {au}, MaxAux: {ma}")
            for i in range(ms + au):
                rec = IndexRecord.unpack(f.read(IndexRecord.SIZE))
                prefix = "[Aux]" if i >= ms else "[Main]"
                print(f"{prefix} {rec.key} -> {rec.offset}")
