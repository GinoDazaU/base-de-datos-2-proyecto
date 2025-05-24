import struct

# Esta clase Record representa un registro binario genérico.
# A diferencia de versiones más rígidas (como las que usan FORMAT fijo),
# esta clase permite definir cualquier combinación de campos y tipos
# mediante un esquema dinámico que se pasa como parámetro.
# Esto permite reutilizar la misma clase para diferentes tablas
# sin necesidad de modificar su definición interna.

# La idea para que esto funcione es darle el esquema al crear cada registro:
# schema = [("id", "i"), ("nombre", "20s"), ("precio", "f"), ("cantidad", "i")]
# values = [3, "Caramelos", 1.75, 25]
# registro = Record(schema, values)

class Record:

    def __init__(self, schema, values):
        self.schema = schema
        self.values = values
        self.format = ''.join(fmt for _, fmt in schema)
        self.size = struct.calcsize(self.format)

    def pack(self) -> bytes:
        processed_values = []
        for (_, fmt), value in zip(self.schema, self.values):
            if 's' in fmt:
                size = int(fmt[:-1])
                value = value.encode('utf-8')[:size].ljust(size, b'\x00')
            processed_values.append(value)
        return struct.pack(self.format, *processed_values)

    @staticmethod
    def unpack(record_buffer, schema):
        format_str = ''.join(fmt for _, fmt in schema)
        values = struct.unpack(format_str, record_buffer)
        processed_values = []
        for (_, fmt), value in zip(schema, values):
            if 's' in fmt:
                value = value.rstrip(b'\x00').decode('utf-8')
            processed_values.append(value)
        return Record(schema, processed_values)
    
    @staticmethod
    def get_size(schema) -> int:
        format_str = ''.join(fmt for _, fmt in schema)
        return struct.calcsize(format_str)

    def print(self) -> None:
        for (_, fmt), value in zip(self.schema, self.values):
            if 'f' in fmt:
                print(f"{value:.2f}", end=" | ")
            else:
                print(value, end=" | ")
        print()

def main():

    # Crear varios registros
    schema = [("id", "i"), ("nombre", "20s"), ("precio", "f"), ("cantidad", "i")]

    values1 = [1, "Galletas", 3.5, 10]
    values2 = [2, "Chocolate", 5.2, 8]
    values3 = [3, "Caramelos", 1.75, 25]
    values4 = [4, "Cereal", 4.0, 12]

    # Crear los objetos Record
    registro1 = Record(schema, values1)
    registro2 = Record(schema, values2)
    registro3 = Record(schema, values3)
    registro4 = Record(schema, values4)

    # Empaquetar y desempacar (simulando lectura binaria)
    registros_bin = [
        registro1.pack(),
        registro2.pack(),
        registro3.pack(),
        registro4.pack()
    ]

    registros = [Record.unpack(bin_data, schema) for bin_data in registros_bin]

    # Mostrar todos los registros
    for r in registros:
        r.print()
