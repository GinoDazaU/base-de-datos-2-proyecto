import struct
import json
import os
from typing import Optional

from .Record import Record

class HeapFile:

    METADATA_FORMAT = "i"
    METADATA_SIZE = struct.calcsize(METADATA_FORMAT)

    def __init__(self, table_name: str) -> None:
        # Inicializa el archivo heap cargando el esquema y el tamaño actual.
        self.filename = table_name + ".dat"
        self.schema = self._load_schema(self.filename)
        self.record_size = Record.get_size(self.schema)
        if os.path.exists(self.filename):
            with open(self.filename, "rb") as f:
                metadata_buffer = f.read(self.METADATA_SIZE)
                self.heap_size = struct.unpack(self.METADATA_FORMAT, metadata_buffer)[0]
        else:
            raise FileNotFoundError(f"El archivo {self.filename} no existe. Crea la tabla primero.")

    @staticmethod
    def build_file(table_name: str, schema: list[tuple[str, str]]) -> None:
        # Crea un nuevo archivo heap vacío y guarda su esquema en un archivo .json.
        filename = table_name + ".dat"
        with open(filename, "wb") as f:
            heap_size = 0
            metadata = struct.pack(HeapFile.METADATA_FORMAT, heap_size)
            f.write(metadata)

        schema_file = table_name + ".schema.json"
        fields = [{"name": name, "type": fmt} for name, fmt in schema]
        schema_json = {
            "table_name": os.path.splitext(os.path.basename(table_name))[0],
            "fields": fields
        }
        with open(schema_file, "w") as f:
            json.dump(schema_json, f, indent=4)

    def _load_schema(self, filename: str) -> list[tuple[str, str]]:
        # Carga el esquema desde un archivo .json asociado al archivo de datos.
        schema_file = filename.replace(".dat", ".schema.json")
        with open(schema_file, "r") as f:
            schema_json = json.load(f)
        return [(field["name"], field["type"]) for field in schema_json["fields"]]

    def update_metadata(self, file_handle: Optional[object] = None) -> None:
        """
        Actualiza el contador de registros en metadata.  
        Si se pasa un file_handle abierto en modo r+b, lo utiliza, sino abre el archivo.
        """
        if file_handle:
            file_handle.seek(0)
            file_handle.write(struct.pack(self.METADATA_FORMAT, self.heap_size))
        else:
            with open(self.filename, "r+b") as f:
                f.seek(0)
                f.write(struct.pack(self.METADATA_FORMAT, self.heap_size))

    def extract_index(self, key_field: str) -> list[tuple[object, int]]:
        """
        Devuelve una lista de tuplas (valor_clave, número_de_registro) del campo clave especificado,
        ignorando registros eliminados si el campo 'id' es -1.
        """
        field_names = [name for name, _ in self.schema]
        if key_field not in field_names:
            raise KeyError(f"Campo '{key_field}' no existe en esquema")
        key_pos = field_names.index(key_field)

        # Asumimos que el campo 'id' (el primero) se usa para detectar eliminados
        id_pos = field_names.index("id") if "id" in field_names else None

        entries: list[tuple[object, int]] = []
        with open(self.filename, "rb") as f:
            f.seek(self.METADATA_SIZE)
            rec_num = 0
            while True:
                buffer = f.read(self.record_size)
                if len(buffer) < self.record_size:
                    break
                rec = Record.unpack(buffer, self.schema)
                if id_pos is not None and isinstance(rec.values[id_pos], int) and rec.values[id_pos] == -1:
                    rec_num += 1
                    continue
                key_val = rec.values[key_pos]
                entries.append((key_val, rec_num))
                rec_num += 1
        return entries

    def insert_record(self, record: Record) -> int:
        """
        Inserta un registro al final y actualiza metadata en el mismo file handle.
        """
        if self.search_record(record.id) != None:
            print("El registro ya existe")
            return False
        if record.schema != self.schema:
            raise ValueError("El esquema del registro no coincide con el esquema del archivo.")
        with open(self.filename, "r+b") as f:
            f.seek(0, os.SEEK_END)
            f.write(record.pack())
            self.heap_size += 1
            self.update_metadata(file_handle=f)
            return self.heap_size - 1

    def search_record(self, target_id: int) -> Optional[Record]:
        # Busca un registro cuyo campo 'id' coincida con `target_id`. Muestra el resultado si se encuentra.
        id_index = None
        for i, (name, _) in enumerate(self.schema):
            if name == "id":
                id_index = i
                break
        if id_index is None:
            print("El campo 'id' no está definido en el esquema.")
            return None

        with open(self.filename, "rb") as f:
            f.seek(self.METADATA_SIZE)
            for i in range(self.heap_size):
                offset = self.METADATA_SIZE + i * self.record_size
                f.seek(offset)
                record_buffer = f.read(self.record_size)
                record = Record.unpack(record_buffer, self.schema)
                record_id = record.values[id_index]

                if str(record_id).strip() == str(target_id).strip():
                    print("Registro encontrado:")
                    record.print()
                    return record
                
        print(f"No se encontró un registro con id = {target_id}")
        return None

    def fetch_record_by_offset(self, rec_num: int) -> Record:
        """
        Devuelve el registro ubicado en el número de registro `rec_num` (offset lógico).  
        Lanza IndexError si `rec_num` fuera de rango.
        """
        if rec_num < 0 or rec_num >= self.heap_size:
            raise IndexError(f"Offset {rec_num} fuera de rango (0..{self.heap_size-1})")
        with open(self.filename, "rb") as f:
            byte_offset = self.METADATA_SIZE + rec_num * self.record_size
            f.seek(byte_offset)
            buffer = f.read(self.record_size)
            return Record.unpack(buffer, self.schema)

    def print_all(self) -> None:
        # Muestra todos los registros del archivo, incluyendo metadata (heap_size).
        print(f"Metadata (heap_size): {self.heap_size}")
        with open(self.filename, "rb") as f:
            f.seek(self.METADATA_SIZE)
            headers = [name for name, _ in self.schema]
            print(" | ".join(headers))
            print("-" * (len(headers) * 10))
            for _ in range(self.heap_size):
                buf = f.read(self.record_size)
                rec = Record.unpack(buf, self.schema)
                rec.print()