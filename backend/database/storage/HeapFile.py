from .Record import Record
import struct
import json
import os

class HeapFile:

    METADATA_FORMAT = "i"
    METADATA_SIZE = struct.calcsize(METADATA_FORMAT)

    def __init__(self, filename):
        self.filename = filename
        self.schema = self.load_schema(filename)
        self.record_size = Record.get_size(self.schema)
        if os.path.exists(filename):
            with open(filename, "rb") as file:
                metadata_buffer= file.read(self.METADATA_SIZE)
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

    def update_metadata(self):
        with open(self.filename, "r+b") as file:
            metadata_buffer = struct.pack(self.METADATA_FORMAT, self.heap_size)
            file.write(metadata_buffer)

    def insert_record(self, record: Record):
        with open(self.filename, "ab") as file:
            file.write(record.pack())
            self.heap_size += 1
        self.update_metadata()
    
    def search_record(self, target_id):
        id_index = None
        for i, (name, _) in enumerate(self.schema):
            if name == "id":
                id_index = i
                break
        if id_index is None:
            print("El campo 'id' no está definido en el esquema.")
            return

        with open(self.filename, "rb") as file:
            file.seek(self.METADATA_SIZE, 0)
            for i in range(self.heap_size):
                offset = self.METADATA_SIZE + i * self.record_size
                file.seek(offset)
                record_buffer = file.read(self.record_size)
                record = Record.unpack(record_buffer, self.schema)
                record_id = record.values[id_index]

                if str(record_id).strip() == str(target_id).strip():
                    print("Registro encontrado:")
                    record.print()
                    return record

        print(f"No se encontró un registro con id = {target_id}")
        return None


    def load(self):
        with open(self.filename, "rb") as file:
            file.seek(self.METADATA_SIZE, 0)
            records = []
            for _ in range(self.heap_size):
                record_buffer = file.read(self.record_size)
                record = Record.unpack(record_buffer, self.schema)
                records.append(record)
            headers = [name for name, _ in self.schema]
            print(" | ".join(headers))
            print("-" * (len(headers) * 10)) 
            for record in records:
                record.print()