import struct
from typing import TextIO, Tuple, Union, List
import os
import pickle
from .IndexRecord import IndexRecord
from . import utils

class Bucket:
    HEADER_FORMAT = "ii"
    HEADER_SIZE = struct.calcsize(HEADER_FORMAT)

    def __init__(self, fb: int, key_format: str):
        self.size = 0
        self.next = -1
        self.records: List[IndexRecord] = []
        self.fb = fb
        self.key_format = key_format
        
        # Crear registros vacíos
        empty_key = utils.get_empty_key(key_format)
        for _ in range(self.fb):
            self.records.append(IndexRecord(key_format, empty_key, -1))

    def pack(self) -> bytes:
        data = b''
        for record in self.records:
            data += record.pack()
        return data + struct.pack(self.HEADER_FORMAT, self.size, self.next)
    
    @staticmethod
    def unpack(packed_data: bytes, fb: int, key_format: str) -> "Bucket":
        record_size = IndexRecord(key_format, utils.get_empty_key(key_format), -1).size
        bucket = Bucket(fb, key_format)
        
        size, next = struct.unpack(Bucket.HEADER_FORMAT, packed_data[-Bucket.HEADER_SIZE:])
        for i in range(size):
            start = i * record_size
            end = (i + 1) * record_size
            record_data = packed_data[start:end]
            bucket.add_record(IndexRecord.unpack(record_data, key_format))
        
        bucket.next = next
        return bucket
    
    def is_full(self) -> bool:
        return self.size == self.fb
    
    def add_record(self, record: IndexRecord):
        if not self.is_full():
            self.records[self.size] = record
            self.size += 1

class Node:
    def __init__(self, left=-1, right=-1):
        self.left = left
        self.right = right
        self.left_is_leaf = True
        self.right_is_leaf = True

    def next(self, val: int) -> Tuple[Union[int, "Node"], bool]:
        return (self.left, self.left_is_leaf) if val == 0 else (self.right, self.right_is_leaf)

    def set_left_value(self, val: int):
        self.left = val
        self.left_is_leaf = True

    def set_right_value(self, val: int):
        self.right = val
        self.right_is_leaf = True

    def set_left_node(self, node: "Node"):
        self.left = node
        self.left_is_leaf = False

    def set_right_node(self, node: "Node"):
        self.right = node
        self.right_is_leaf = False

class ExtendibleHashIndex:
    HEADER_FORMAT = "iiii"
    HEADER_SIZE = struct.calcsize(HEADER_FORMAT)

    def __init__(self, table_name: str, indexed_field: str, D: int = 3, fb: int = 4):

        self.filename = f"{table_name}.{indexed_field}.hash.idx"
        self.hash_file = f"{table_name}.{indexed_field}.hash.tree"

        if not os.path.exists(self.filename):
            raise FileNotFoundError(f"El índice hash para {table_name} no existe. Crea el índice primero.")
        
        # Cargar schema para determinar formato de la clave
        self.schema = utils.load_schema(table_name)
        self.key_field = indexed_field
        self.key_format = utils.get_key_format_from_schema(self.schema, self.key_field)
        
        # Crear registro de muestra para calcular tamaños
        sample_record = IndexRecord(self.key_format, utils.get_empty_key(self.key_format), -1)
        self.record_size = sample_record.size
        
        # Cargar índice existente
        with open(self.filename, "rb") as file:
            self.D, self.BUCKETS, self.OVERFLOW_BUCKETS, self.fb = struct.unpack(
                self.HEADER_FORMAT, file.read(self.HEADER_SIZE))
        
        with open(self.hash_file, "rb") as hfile:
            self.hash_tree = pickle.load(hfile)
        
        self.BUCKET_SIZE = self.fb * self.record_size + Bucket.HEADER_SIZE
        self.MAX_BUCKETS = 2**self.D

    @staticmethod
    def build_index(heap_filename: str, extract_index_fn, key_field: str, D: int = 3, fb: int = 4):
        """
        Construye un nuevo índice de hash extensible para el campo especificado.
        """
        # Cargar schema para validación
        schema = utils.load_schema(heap_filename)
        key_format = utils.get_key_format_from_schema(schema, key_field)
        
        # Obtener y validar entradas
        entries = extract_index_fn(key_field)
        valid_entries = [(k, o) for k, o in entries if IndexRecord._validate_type(k, key_format)]
        
        # Crear índice
        index = ExtendibleHashIndex(
            table_name=heap_filename,
            indexed_field=key_field,
            D=D,
            fb=fb
        )
        
        # Insertar registros
        for key, offset in valid_entries:
            record = IndexRecord(key_format, key, offset)
            index.insert_record(record)
        
        return True

    def write_headers(self, file: TextIO):
        file.seek(0)
        file.write(struct.pack(
            self.HEADER_FORMAT, 
            self.D, 
            self.BUCKETS, 
            self.OVERFLOW_BUCKETS, 
            self.fb
        ))

    def write_hash_index(self):
        with open(self.hash_file, "wb") as hfile:
            pickle.dump(self.hash_tree, hfile)
    
    def hash(self, key: Union[int, float, str]) -> int:
        """Función hash adaptada al tipo de clave."""
        if self.key_format == 'i':
            return key % self.MAX_BUCKETS
        elif self.key_format == 'f':
            return int(key) % self.MAX_BUCKETS
        elif 's' in self.key_format:
            return sum(ord(c) for c in str(key)) % self.MAX_BUCKETS
    
    def binary(self, num: int) -> str:
        """Representación binaria con padding a D bits."""
        return bin(num)[2:].zfill(self.D)
    
    def read_bucket(self, file: TextIO, bucket_pos: int) -> Bucket:
        file.seek(self.BUCKET_SIZE * bucket_pos + self.HEADER_SIZE)
        return Bucket.unpack(file.read(self.BUCKET_SIZE), self.fb, self.key_format)
    
    def write_bucket(self, file: TextIO, bucket_pos: int, bucket: Bucket):
        file.seek(self.BUCKET_SIZE * bucket_pos + self.HEADER_SIZE)
        file.write(bucket.pack())

    def insert_record(self, record: IndexRecord):
        """Inserta un nuevo registro en el índice."""
        if record.format != self.key_format:
            raise TypeError(f"El registro tiene formato {record.format}, se esperaba {self.key_format}")
        
        with open(self.filename, "r+b") as file:
            binary = self.binary(self.hash(record.key))
            
            node = self.hash_tree
            local_depth = 0
            bucket_pos = -1
            
            # Navegar por el árbol para encontrar el bucket
            while True:
                local_depth += 1
                next_pos, is_leaf = node.next(int(binary[local_depth - 1], 2))
                if is_leaf:
                    bucket_pos = next_pos
                    break
                else:
                    node = next_pos
            
            bucket = self.read_bucket(file, bucket_pos)
            
            # Verificar si el registro ya existe
            for i in range(bucket.size):
                if bucket.records[i].key == record.key and bucket.records[i].offset == record.offset:
                    return  # Registro duplicado
            
            if bucket.is_full():
                if local_depth == self.D:  # Overflow
                    self._handle_overflow(file, bucket, bucket_pos, record)
                else:  # Split
                    self._handle_split(file, node, bucket, bucket_pos, record, binary, local_depth)
            else:
                bucket.add_record(record)
                self.write_bucket(file, bucket_pos, bucket)

    def _handle_overflow(self, file, bucket, bucket_pos, record):
        """Maneja el caso de overflow creando un nuevo bucket de overflow."""
        # Buscar el último bucket en la cadena
        while bucket.next != -1:
            bucket_pos = bucket.next
            bucket = self.read_bucket(file, bucket_pos)
        
        if bucket.is_full():
            # Crear nuevo bucket de overflow
            new_bucket_pos = self.BUCKETS + self.OVERFLOW_BUCKETS
            new_bucket = Bucket(self.fb, self.key_format)
            new_bucket.add_record(record)
            bucket.next = new_bucket_pos
            
            self.write_bucket(file, bucket_pos, bucket)
            self.write_bucket(file, new_bucket_pos, new_bucket)
            
            self.OVERFLOW_BUCKETS += 1
            self.write_headers(file)
        else:
            bucket.add_record(record)
            self.write_bucket(file, bucket_pos, bucket)

    def _handle_split(self, file, node, bucket, bucket_pos, record, binary, local_depth):
        """Maneja el split de buckets cuando es necesario."""
        records_to_redistribute = bucket.records[:bucket.size]
        records_to_redistribute.append(record)
        
        # Crear nuevo bucket
        new_bucket_pos = self.BUCKETS + self.OVERFLOW_BUCKETS
        new_bucket = Bucket(self.fb, self.key_format)
        
        # Vaciar bucket original
        bucket.size = 0
        bucket.next = -1
        
        # Redistribuir registros
        for rec in records_to_redistribute:
            target_bucket = bucket if self._should_go_left(rec.key, binary, local_depth) else new_bucket
            if target_bucket.is_full():
                # Manejar overflow durante redistribución
                self._handle_overflow(file, target_bucket, 
                                    bucket_pos if target_bucket == bucket else new_bucket_pos, 
                                    rec)
            else:
                target_bucket.add_record(rec)
        
        # Actualizar árbol
        new_node = Node(bucket_pos, new_bucket_pos)
        if binary[local_depth] == '0':
            node.set_left_node(new_node)
        else:
            node.set_right_node(new_node)
        
        self.write_hash_index()
        self.BUCKETS += 1
        self.write_headers(file)
        self.write_bucket(file, bucket_pos, bucket)
        self.write_bucket(file, new_bucket_pos, new_bucket)

    def _should_go_left(self, key, binary, local_depth):
        """Determina si un registro debe ir al bucket izquierdo después del split."""
        key_binary = self.binary(self.hash(key))
        return key_binary[:local_depth + 1] == binary[:local_depth] + '0'

    def search_record(self, key: Union[int, float, str]) -> List[IndexRecord]:
        """Busca todos los registros con la clave especificada."""
        if not IndexRecord._validate_type(key, self.key_format):
            raise TypeError(f"Clave {key} no es del tipo {self.key_format}")
        
        results = []
        with open(self.filename, "rb") as file:
            binary = self.binary(self.hash(key))
            
            node = self.hash_tree
            local_depth = 0
            bucket_pos = -1
            
            # Navegar por el árbol
            while True:
                local_depth += 1
                next_pos, is_leaf = node.next(int(binary[local_depth - 1], 2))
                if is_leaf:
                    bucket_pos = next_pos
                    break
                else:
                    node = next_pos
            
            # Buscar en la cadena de buckets
            while bucket_pos != -1:
                bucket = self.read_bucket(file, bucket_pos)
                for i in range(bucket.size):
                    if bucket.records[i].key == key:
                        results.append(bucket.records[i])
                bucket_pos = bucket.next
        
        return results

    def delete_record(self, key: Union[int, float, str], offset: int = None) -> bool:
        """Elimina un registro del índice."""
        if not IndexRecord._validate_type(key, self.key_format):
            raise TypeError(f"Clave {key} no es del tipo {self.key_format}")
        
        deleted = False
        with open(self.filename, "r+b") as file:
            binary = self.binary(self.hash(key))
            
            node = self.hash_tree
            local_depth = 0
            bucket_pos = -1
            
            # Navegar por el árbol
            while True:
                local_depth += 1
                next_pos, is_leaf = node.next(int(binary[local_depth - 1], 2))
                if is_leaf:
                    bucket_pos = next_pos
                    break
                else:
                    node = next_pos
            
            # Buscar en la cadena de buckets
            while bucket_pos != -1:
                bucket = self.read_bucket(file, bucket_pos)
                for i in range(bucket.size):
                    if bucket.records[i].key == key and (offset is None or bucket.records[i].offset == offset):
                        # Marcar como eliminado (usando valores especiales)
                        empty_key = utils.get_empty_key(self.key_format)
                        bucket.records[i] = IndexRecord(self.key_format, empty_key, -1)
                        deleted = True
                        self.write_bucket(file, bucket_pos, bucket)
                        break
                bucket_pos = bucket.next
        
        return deleted

    def print_all(self):
        """Imprime todos los registros del índice."""
        with open(self.filename, "rb") as file:
            # Leer metadatos
            self.D, self.BUCKETS, self.OVERFLOW_BUCKETS, self.fb = struct.unpack(
                self.HEADER_FORMAT, file.read(self.HEADER_SIZE))
            
            print(f"Metadata: D={self.D}, Buckets={self.BUCKETS}, Overflow={self.OVERFLOW_BUCKETS}, fb={self.fb}")
            print("Key format:", self.key_format)
            print("-" * 50)
            
            # Leer buckets principales
            print("[MAIN BUCKETS]")
            for i in range(self.BUCKETS):
                file.seek(self.HEADER_SIZE + i * self.BUCKET_SIZE)
                bucket = Bucket.unpack(file.read(self.BUCKET_SIZE), self.fb, self.key_format)
                print(f"Bucket {i}: Size={bucket.size}, Next={bucket.next}")
                for j in range(bucket.size):
                    rec = bucket.records[j]
                    status = "DELETED" if self._is_deleted(rec) else "ACTIVE"
                    print(f"  Pos {j}: Key={rec.key}, Offset={rec.offset} [{status}]")
            
            # Leer buckets de overflow
            print("\n[OVERFLOW BUCKETS]")
            for i in range(self.OVERFLOW_BUCKETS):
                pos = self.BUCKETS + i
                file.seek(self.HEADER_SIZE + pos * self.BUCKET_SIZE)
                bucket = Bucket.unpack(file.read(self.BUCKET_SIZE), self.fb, self.key_format)
                print(f"Bucket {pos}: Size={bucket.size}, Next={bucket.next}")
                for j in range(bucket.size):
                    rec = bucket.records[j]
                    status = "DELETED" if self._is_deleted(rec) else "ACTIVE"
                    print(f"  Pos {j}: Key={rec.key}, Offset={rec.offset} [{status}]")

    def _is_deleted(self, record: IndexRecord) -> bool:
        """Determina si un registro está marcado como eliminado."""
        if self.key_format == 'i':
            return record.key == -1
        elif self.key_format == 'f':
            return record.key == -1.0
        elif 's' in self.key_format:
            return record.key == ''
        return False