import struct
from future.schema import SchemaType
from future.primitives import Varchar

class NewRecord:
    def __init__(self, schema:SchemaType, values: list):
        self.schema = schema
        self.values = values
        self.FORMAT = ''.join(fmt for name, fmt in schema)
        self.size = struct.calcsize(self.FORMAT)

    def pack(self) -> bytes:
        processed_values = []
        for (name, fmt), value in zip(self.schema, self.values):
            if 's' in fmt: # for varchars
                size = int(fmt[:-1])
                value = value.encode('utf-8')[:size].ljust(size, b'\x00')
            processed_values.append(value)
        return struct.pack(self.format, *processed_values)

    @staticmethod
    def unpack(record_buffer: bytes, schema: SchemaType):
        FORMAT = ''.join(fmt for _, fmt in schema)
        values = struct.unpack(FORMAT, record_buffer)
        processed_values = []
        for (_, fmt), value in zip(schema, values):
            if 's' in fmt:
                value = value.rstrip(b'\x00').decode('utf-8')
                value = Varchar(value, int(fmt[:-1])) # wraps str in varchar
            processed_values.append(value)
        return NewRecord(schema, processed_values)

    @staticmethod
    def get_size(record: "NewRecord") -> int:
        return struct.calcsize(record.FORMAT)
    
    def __repr__(self) -> None:
        return f"NewRecord({self.schema}, {self.values})"