import struct

class IndexRecord:

    FORMAT = "ii"
    SIZE = struct.calcsize(FORMAT)

    def __init__(self, key, offset):
        self.key = key
        self.offset = offset

    def pack(self) -> bytes:
        index_record_buffer = struct.pack(self.FORMAT, self.key, self.offset)
        return index_record_buffer

    @staticmethod
    def unpack(index_record_buffer: bytes):
        index_record_data = struct.unpack(IndexRecord.FORMAT, index_record_buffer)
        index_record = IndexRecord(index_record_data[0], index_record_data[1])
        return index_record