import struct
import os
import pickle
from typing import TextIO, Tuple, Union, Any, List

class HashRecord:
    """Registro para el índice hash que almacena clave y offset"""
    FORMAT = "qi"  # clave (long long), offset (int)
    SIZE = struct.calcsize(FORMAT)
    
    def __init__(self, key: int, offset: int):
        self.key = key  # Hash de la clave real
        self.offset = offset
        
    def pack(self) -> bytes:
        return struct.pack(self.FORMAT, self.key, self.offset)
    
    @staticmethod
    def unpack(data: bytes) -> 'HashRecord':
        key, offset = struct.unpack(HashRecord.FORMAT, data)
        return HashRecord(key, offset)

class HashBucket:
    """Bucket para el índice hash extendible"""
    HEADER_FORMAT = "ii"  # size (int), next (int)
    HEADER_SIZE = struct.calcsize(HEADER_FORMAT)
    
    def __init__(self, bucket_size: int):
        self.records: List[HashRecord] = []
        self.next = -1  # Para overflow buckets
        self.bucket_size = bucket_size
        
    def is_full(self) -> bool:
        return len(self.records) >= self.bucket_size
        
    def add_record(self, record: HashRecord) -> bool:
        """Añade un registro si hay espacio. Devuelve True si se añadió"""
        if not self.is_full():
            self.records.append(record)
            return True
        return False
        
    def pack(self) -> bytes:
        """Serializa el bucket a bytes"""
        data = b''.join(rec.pack() for rec in self.records)
        # Rellenar con registros vacíos si no está lleno
        empty_rec = HashRecord(0, 0).pack()
        data += empty_rec * (self.bucket_size - len(self.records))
        # Añadir header
        data += struct.pack(self.HEADER_FORMAT, len(self.records), self.next)
        return data
        
    @staticmethod
    def unpack(data: bytes, bucket_size: int) -> 'HashBucket':
        """Deserializa un bucket desde bytes"""
        bucket = HashBucket(bucket_size)
        # Leer registros
        record_size = HashRecord.SIZE
        for i in range(bucket_size):
            start = i * record_size
            rec_data = data[start:start+record_size]
            record = HashRecord.unpack(rec_data)
            if record.key != 0:  # Ignorar registros vacíos
                bucket.records.append(record)
        # Leer header
        header_start = bucket_size * record_size
        bucket.size, bucket.next = struct.unpack(HashBucket.HEADER_FORMAT, 
                                               data[header_start:header_start+HashBucket.HEADER_SIZE])
        return bucket

class HashIndex:
    """Índice hash extendible para cualquier campo"""
    HEADER_FORMAT = "iiii"  # D (int), buckets (int), overflow_buckets (int), bucket_size (int)
    HEADER_SIZE = struct.calcsize(HEADER_FORMAT)
    
    def __init__(self, filename: str, field_name: str, bucket_size: int = 4):
        """
        Inicializa el índice hash.
        
        Args:
            filename: Nombre del archivo de datos (sin extensión)
            field_name: Nombre del campo a indexar
            bucket_size: Número de registros por bucket
        """
        self.filename = f"{filename}.{field_name}.hash.idx"
        self.field_name = field_name
        self.bucket_size = bucket_size
        
        if os.path.exists(self.filename):
            self._load_existing()
        else:
            self._initialize_new()
    
    def _initialize_new(self):
        """Inicializa un nuevo índice vacío"""
        self.D = 1  # Profundidad global
        self.buckets = 2  # Cubos iniciales
        self.overflow_buckets = 0
        self.directory = {0: 0, 1: 1}  # Mapeo hash -> bucket
        
        # Crear buckets iniciales
        with open(self.filename, "wb") as f:
            self._write_headers(f)
            for _ in range(self.buckets):
                bucket = HashBucket(self.bucket_size)
                f.write(bucket.pack())
    
    def _load_existing(self):
        """Carga un índice existente desde disco"""
        with open(self.filename, "rb") as f:
            # Leer headers
            self.D, self.buckets, self.overflow_buckets, self.bucket_size = \
                struct.unpack(self.HEADER_FORMAT, f.read(self.HEADER_SIZE))
            
            # Reconstruir directorio (simplificado)
            self.directory = {}
            for i in range(2**self.D):
                self.directory[i] = i % self.buckets
    
    def _write_headers(self, file: TextIO):
        """Escribe los headers del archivo"""
        file.seek(0)
        file.write(struct.pack(self.HEADER_FORMAT, 
                  self.D, self.buckets, self.overflow_buckets, self.bucket_size))
    
    def _hash_key(self, key: Any) -> int:
        """Calcula el hash de una clave (soporta múltiples tipos)"""
        if isinstance(key, int):
            return key
        elif isinstance(key, float):
            return struct.unpack('i', struct.pack('f', key))[0]
        elif isinstance(key, str):
            return hash(key)  # Usamos el hash de Python para strings
        else:
            raise TypeError(f"Tipo de clave no soportado: {type(key)}")
    
    def _get_bucket_pos(self, hashed_key: int) -> int:
        """Obtiene la posición del bucket para una clave hasheada"""
        mask = (1 << self.D) - 1
        return self.directory[hashed_key & mask]
    
    def insert(self, key: Any, offset: int):
        """Inserta una clave con su offset en el índice"""
        hashed_key = self._hash_key(key)
        
        with open(self.filename, "r+b") as f:
            bucket_pos = self._get_bucket_pos(hashed_key)
            f.seek(self.HEADER_SIZE + bucket_pos * self._bucket_total_size())
            bucket_data = f.read(self._bucket_total_size())
            bucket = HashBucket.unpack(bucket_data, self.bucket_size)
            
            # Verificar si la clave ya existe
            for record in bucket.records:
                if record.key == hashed_key and record.offset == offset:
                    return  # Ya existe
                
            # Intentar insertar
            if not bucket.is_full():
                bucket.add_record(HashRecord(hashed_key, offset))
                f.seek(self.HEADER_SIZE + bucket_pos * self._bucket_total_size())
                f.write(bucket.pack())
                return
            
            # Manejar overflow (simplificado)
            self._handle_overflow(f, bucket_pos, hashed_key, offset)
    
    def _bucket_total_size(self) -> int:
        """Tamaño total de un bucket en bytes"""
        return self.bucket_size * HashRecord.SIZE + HashBucket.HEADER_SIZE
    
    def _handle_overflow(self, file: TextIO, bucket_pos: int, hashed_key: int, offset: int):
        """Maneja un bucket lleno (versión simplificada)"""
        # Buscar o crear bucket de overflow
        file.seek(self.HEADER_SIZE + bucket_pos * self._bucket_total_size())
        bucket_data = file.read(self._bucket_total_size())
        bucket = HashBucket.unpack(bucket_data, self.bucket_size)
        
        while bucket.next != -1:
            file.seek(self.HEADER_SIZE + bucket.next * self._bucket_total_size())
            bucket_data = file.read(self._bucket_total_size())
            bucket = HashBucket.unpack(bucket_data, self.bucket_size)
        
        if bucket.is_full():
            # Crear nuevo bucket de overflow
            new_bucket_pos = self.buckets + self.overflow_buckets
            new_bucket = HashBucket(self.bucket_size)
            new_bucket.add_record(HashRecord(hashed_key, offset))
            
            bucket.next = new_bucket_pos
            self.overflow_buckets += 1
            
            # Escribir buckets
            file.seek(self.HEADER_SIZE + bucket_pos * self._bucket_total_size())
            file.write(bucket.pack())
            
            file.seek(0, 2)  # Ir al final del archivo
            file.write(new_bucket.pack())
            
            self._write_headers(file)
        else:
            bucket.add_record(HashRecord(hashed_key, offset))
            file.seek(self.HEADER_SIZE + bucket_pos * self._bucket_total_size())
            file.write(bucket.pack())
    
    def search(self, key: Any) -> List[int]:
        """Busca todos los offsets para una clave dada"""
        hashed_key = self._hash_key(key)
        offsets = []
        
        with open(self.filename, "rb") as f:
            bucket_pos = self._get_bucket_pos(hashed_key)
            
            while bucket_pos != -1:
                f.seek(self.HEADER_SIZE + bucket_pos * self._bucket_total_size())
                bucket_data = f.read(self._bucket_total_size())
                bucket = HashBucket.unpack(bucket_data, self.bucket_size)
                
                for record in bucket.records:
                    if record.key == hashed_key:
                        offsets.append(record.offset)
                
                bucket_pos = bucket.next
        
        return offsets