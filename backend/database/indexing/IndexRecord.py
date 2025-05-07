import struct
from typing import Union, Tuple
import math

class IndexRecord:
    """Registro de índice que soporta claves de tipo int, float o string."""
    
    # Tipos soportados
    TYPE_INT = 0
    TYPE_FLOAT = 1
    TYPE_STRING = 2
    
    def __init__(self, format: str, key: Union[int, float, str], offset: int):
        """
        Inicializa el registro de índice.
        
        Args:
            format: Formato del campo ('i', 'f', o 'Ns' donde N es tamaño string)
            key: Valor de la clave
            offset: Posición en el archivo de datos
        """
        self.format = format
        self.key = key
        self.offset = offset
        self._validate_types()
        
    def _validate_types(self):
        """Valida que los tipos coincidan con el formato especificado."""
        if self.format == 'i' and not isinstance(self.key, int):
            raise TypeError(f"Clave debe ser int para formato 'i', se recibió {type(self.key)}")
        elif self.format == 'f' and not isinstance(self.key, float):
            raise TypeError(f"Clave debe ser float para formato 'f', se recibió {type(self.key)}")
        elif 's' in self.format:
            if not isinstance(self.key, str):
                raise TypeError(f"Clave debe ser str para formato string, se recibió {type(self.key)}")
            try:
                size = int(self.format[:-1])
            except ValueError:
                raise ValueError(f"Formato string debe ser 'Ns' (ej: '10s'), se recibió '{self.format}'")
    
    def pack(self) -> bytes:
        """Serializa el registro a bytes."""
        if self.format == 'i':
            return struct.pack(f"Bii", self.TYPE_INT, self.key, self.offset)
        elif self.format == 'f':
            return struct.pack(f"Bfi", self.TYPE_FLOAT, self.key, self.offset)
        elif 's' in self.format:
            size = int(self.format[:-1])
            encoded = self.key.encode('utf-8')[:size].ljust(size, b'\x00')
            return struct.pack(f"B{size}si", self.TYPE_STRING, encoded, self.offset)
        else:
            raise ValueError(f"Formato no soportado: '{self.format}'")

    @staticmethod
    def unpack(data: bytes, format: str) -> 'IndexRecord':
        """Deserializa un registro desde bytes."""
        type_byte = data[0]
        
        if type_byte == IndexRecord.TYPE_INT:
            _, key, offset = struct.unpack_from("Bii", data)
            return IndexRecord('i', key, offset)
        elif type_byte == IndexRecord.TYPE_FLOAT:
            _, key, offset = struct.unpack_from("Bfi", data)
            return IndexRecord('f', key, offset)
        elif type_byte == IndexRecord.TYPE_STRING:
            if 's' not in format:
                raise ValueError("Se esperaba formato string para deserialización")
            size = int(format[:-1])
            fmt = f"B{size}si"
            _, encoded, offset = struct.unpack_from(fmt, data)
            key = encoded.decode('utf-8').rstrip('\x00')
            return IndexRecord(format, key, offset)
        else:
            raise ValueError(f"Tipo de registro desconocido: {type_byte}")

    @property
    def size(self) -> int:
        """Tamaño en bytes del registro serializado."""
        if self.format == 'i':
            return struct.calcsize("Bii")
        elif self.format == 'f':
            return struct.calcsize("Bfi")
        elif 's' in self.format:
            size = int(self.format[:-1])
            return struct.calcsize(f"B{size}si")
    
    def __eq__(self, other: 'IndexRecord') -> bool:
        """Comparación por igualdad."""
        return self.key == other.key and self.offset == other.offset
    
    def __lt__(self, other: 'IndexRecord') -> bool:
        """Comparación menor que para ordenamiento."""
        if not isinstance(other, IndexRecord):
            raise TypeError("Comparación solo válida entre IndexRecords")
        return self.key < other.key
    
    def __repr__(self) -> str:
        return f"IndexRecord(format='{self.format}', key={self.key}, offset={self.offset})"