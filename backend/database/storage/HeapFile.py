import struct
import json
import os
from .Record import Record

class HeapFile:

    METADATA_FORMAT = "i"
    METADATA_SIZE = struct.calcsize(METADATA_FORMAT)

    def __init__(self, filename):
        self.filename = filename
        self.schema = self.load_schema(filename)
        self.record_size = Record.get_size(self.schema)
        if os.path.exists(filename):
            with open(filename, "rb") as file:
                metadata_buffer = file.read(self.METADATA_SIZE)
                self.heap_size = struct.unpack(self.METADATA_FORMAT, metadata_buffer)[0]
        else:
            raise FileNotFoundError(f"El archivo {filename} no existe. Crea la tabla primero.")

    @staticmethod
    def build_file(filename, schema):
        with open(filename, "wb") as f:
            heap_size = 0
            metadata = struct.pack(HeapFile.METADATA_FORMAT, heap_size)
            f.write(metadata)

        schema_file = filename.replace(".dat", ".schema.json")
        fields = [{"name": name, "type": fmt} for name, fmt in schema]
        schema_json = {
            "table_name": os.path.splitext(os.path.basename(filename))[0],
            "fields": fields
        }
        with open(schema_file, "w") as f:
            json.dump(schema_json, f, indent=4)

    def load_schema(self, filename):
        schema_file = filename.replace(".dat", ".schema.json")
        with open(schema_file, "r") as file:
            schema_json = json.load(file)
        return [(field["name"], field["type"]) for field in schema_json["fields"]]

    def update_metadata(self, file_handle=None):
        if file_handle:
            file_handle.seek(0)
            file_handle.write(struct.pack(self.METADATA_FORMAT, self.heap_size))
        else:
            with open(self.filename, "r+b") as file:
                file.seek(0)
                file.write(struct.pack(self.METADATA_FORMAT, self.heap_size))

    def extract_index(self, key_field: str) -> list[tuple[int,int]]:
        field_names = [name for name, _ in self.schema]
        if key_field not in field_names:
            raise KeyError(f"Campo '{key_field}' no existe en esquema")
        key_pos = field_names.index(key_field)

        entries: list[tuple[int,int]] = []
        with open(self.filename, "rb") as f:
            f.seek(self.METADATA_SIZE)
            rec_num = 0
            while True:
                buf = f.read(self.record_size)
                if len(buf) < self.record_size:
                    break
                rec = Record.unpack(buf, self.schema)
                key_val = rec.values[key_pos]
                if isinstance(key_val, int) and key_val != -1:
                    entries.append((key_val, rec_num))
                rec_num += 1
        return entries

    def insert_record(self, record: Record):
        if record.schema != self.schema:
            raise ValueError("El esquema del registro no coincide con el esquema del archivo.")
        with open(self.filename, "r+b") as file:
            # Mover al final para escritura
            file.seek(0, os.SEEK_END)
            file.write(record.pack())
            self.heap_size += 1
            # Actualizar metadata sin reabrir archivo
            self.update_metadata(file_handle=file)

    def search_record(self, target_id):
        id_index = None
        for i, (name, _) in enumerate(self.schema):
            if name == "id":
                id_index = i
                break
        if id_index is None:
            print("El campo 'id' no está definido en el esquema.")
            return None

        with open(self.filename, "rb") as file:
            file.seek(self.METADATA_SIZE)
            for i in range(self.heap_size):
                offset = self.METADATA_SIZE + i * self.record_size
                file.seek(offset)
                record_buffer = file.read(self.record_size)
                rec = Record.unpack(record_buffer, self.schema)
                if rec.values[id_index] == target_id:
                    print("Registro encontrado:")
                    rec.print()
                    return rec
        print(f"No se encontró un registro con id = {target_id}")
        return None

    def search_record_by_offset(self, rec_num: int) -> Record:
        if rec_num < 0 or rec_num >= self.heap_size:
            raise IndexError(f"Offset {rec_num} fuera de rango (0..{self.heap_size-1})")
        with open(self.filename, "rb") as file:
            byte_offset = self.METADATA_SIZE + rec_num * self.record_size
            file.seek(byte_offset)
            buffer = file.read(self.record_size)
            return Record.unpack(buffer, self.schema)

    def load(self):
        with open(self.filename, "rb") as file:
            file.seek(self.METADATA_SIZE)
            headers = [name for name, _ in self.schema]
            print(" | ".join(headers))
            print("-" * (len(headers) * 10))
            for i in range(self.heap_size):
                buf = file.read(self.record_size)
                rec = Record.unpack(buf, self.schema)
                rec.print()
