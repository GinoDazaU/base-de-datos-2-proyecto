from .IndexRecord import IndexRecord
import struct
import os

class BPlusTreeIndex:
    
    def __init__(self, table_name: str, indexed_file: str):
        self.filename = table_name + "." + indexed_file + ".btree.idx"



FORMAT = 'i20si'
RECORD_SIZE = struct.calcsize(FORMAT)
NODE_HEADER_FORMAT = 'iiQ'  # is_leaf, key_count, next_leaf_offset

class Record:
    def __init__(self, id, nombre, ciclo):
        self.id = id
        self.nombre = nombre
        self.ciclo = ciclo

    def to_bytes(self):
        nombre_bytes = self.nombre.encode('utf-8')[:20].ljust(20, b'\x00')
        return struct.pack(FORMAT, self.id, nombre_bytes, self.ciclo)

    @staticmethod
    def from_bytes(data):
        id, nombre_bytes, ciclo = struct.unpack(FORMAT, data)
        return Record(id, nombre_bytes.decode('utf-8').strip('\x00'), ciclo)

class BPlusTreeNode:
    def __init__(self, is_leaf=False):
        self.is_leaf = is_leaf

        if is_leaf:
            self.records = []      # List[IndexRecord] en hojas
            self.next = None       
        else:
            self.keys = []         
            self.children = []     
   

class BPlusTree:
    def __init__(self, order, filename, auxname, index_format='i'):
        self.order = order
        self.max_keys = order
        self.node_size = 16 + 4 * self.max_keys + 8 * (self.max_keys + 1)
        self.filename = filename
        self.auxname = auxname
        self.index_format = index_format  # tipo de indice

        try:
            with open(self.auxname, 'rb') as f:
                self.root_offset = struct.unpack('Q', f.read(8))[0]
        except (FileNotFoundError, struct.error):
            root = BPlusTreeNode(is_leaf=True)

            with open(self.auxname, 'wb') as f:
                f.write(struct.pack('Q', 0))

            self.root_offset = self.save_node(root)

            self.update_root_offset(self.root_offset)

    def load_node(self, node_offset):
        with open(self.auxname, 'rb') as f:
            f.seek(node_offset)
            buffer = f.read(self.node_size)

        is_leaf, key_count, next_leaf = struct.unpack('iiQ', buffer[:16])

        node = BPlusTreeNode(is_leaf=bool(is_leaf))

        if is_leaf:
            record_size = IndexRecord(self.index_format, 0, 0).size
            node.records = []
            for i in range(key_count):
                start = 16 + i * record_size
                end = start + record_size
                record_data = buffer[start:end]
                record = IndexRecord.unpack(record_data, self.index_format)
                node.records.append(record)
            node.next = next_leaf
        else:
            keys_start = 16
            keys_size = 4 * self.max_keys
            keys = list(struct.unpack(f'{self.max_keys}i', buffer[keys_start:keys_start + keys_size]))

            children_start = keys_start + keys_size
            children = list(struct.unpack(
                f'{self.max_keys + 1}Q',
                buffer[children_start:children_start + 8 * (self.max_keys + 1)]
            ))

            node.keys = keys[:key_count]
            node.children = children[:key_count + 1]

        return node

    def save_node(self, node):
        is_leaf = int(node.is_leaf)
        key_count = len(node.records if node.is_leaf else node.keys)
        next_leaf = node.next if (node.is_leaf and node.next is not None) else 0

        header = struct.pack('iiQ', is_leaf, key_count, next_leaf)

        if node.is_leaf:
            records_bytes = b''.join(record.pack() for record in node.records)
            padding = b'\x00' * (self.node_size - 16 - len(records_bytes))  # 16 = header size
            buffer = header + records_bytes + padding
        else:
            keys = node.keys + [0] * (self.max_keys - len(node.keys))
            children = node.children + [0] * (self.max_keys + 1 - len(node.children))

            key_data = struct.pack(f'{self.max_keys}i', *keys)
            child_data = struct.pack(f'{self.max_keys + 1}Q', *children)
            buffer = header + key_data + child_data
            buffer += b'\x00' * (self.node_size - len(buffer))

        with open(self.auxname, 'ab') as f:
            pos = f.tell()
            f.write(buffer)
            return pos

        
    def save_node_at(self, offset, node):
        is_leaf = int(node.is_leaf)
        key_count = len(node.records if node.is_leaf else node.keys)
        next_leaf = node.next if (node.is_leaf and node.next is not None) else 0

        header = struct.pack('iiQ', is_leaf, key_count, next_leaf)

        if node.is_leaf:
            # Pack IndexRecord objects
            records_bytes = b''.join(record.pack() for record in node.records)
            padding = b'\x00' * (self.node_size - 16 - len(records_bytes))  # 16 = header size
            buffer = header + records_bytes + padding
        else:
            # Pack keys and children as before
            keys = node.keys + [0] * (self.max_keys - len(node.keys))
            children = node.children + [0] * ((self.max_keys + 1) - len(node.children))

            key_data = struct.pack(f'{self.max_keys}i', *keys)
            child_data = struct.pack(f'{self.max_keys + 1}Q', *children)
            buffer = header + key_data + child_data
            buffer += b'\x00' * (self.node_size - len(buffer))

        with open(self.auxname, 'r+b') as f:
            f.seek(offset)
            f.write(buffer)
        
    def update_root_offset(self, offset):
        with open(self.auxname, 'r+b') as f:
            f.seek(0)
            f.write(struct.pack('Q', offset))
        self.root_offset = offset

    def insert(self, record):
        with open(self.filename, 'ab') as file:
            pos = file.tell()
            file.write(record.to_bytes())

        index_record = IndexRecord(self.index_format, record.id, pos)
        result = self._insert_aux(self.root_offset, index_record)

        if result:
            new_node_offset, separator_key = result
            new_root = BPlusTreeNode(is_leaf=False)
            new_root.keys = [separator_key]
            new_root.children = [self.root_offset, new_node_offset]
            new_root_offset = self.save_node(new_root)
            self.update_root_offset(new_root_offset)

    def _insert_aux(self, node_offset, index_record):
        node = self.load_node(node_offset)

        if node.is_leaf:
            idx = 0
            while idx < len(node.records) and index_record.key > node.records[idx].key:
                idx += 1
            node.records.insert(idx, index_record)

            if len(node.records) > self.order:
                return self._split_leaf(node, node_offset)
            else:
                self.save_node_at(node_offset, node)
                return None

        else:
            idx = 0
            while idx < len(node.keys) and index_record.key > node.keys[idx]:
                idx += 1
            result = self._insert_aux(node.children[idx], index_record)

            if result:
                new_node_offset, new_key = result
                node.keys.insert(idx, new_key)
                node.children.insert(idx + 1, new_node_offset)

                if len(node.keys) > self.order:
                    return self._split_internal(node, node_offset)
                else:
                    self.save_node_at(node_offset, node)
                    return None
            else:
                return None


    def _split_leaf(self, node, node_offset):
        mid = len(node.records) // 2

        new_leaf = BPlusTreeNode(is_leaf=True)
        new_leaf.records = node.records[mid:]
        new_leaf.next = node.next

        node.records = node.records[:mid]
        node.next = self.save_node(new_leaf)

        new_leaf_offset = node.next
        self.save_node_at(node_offset, node)

        return new_leaf_offset, new_leaf.records[0].key

    def _split_internal(self, node, node_offset):
        mid = len(node.keys) // 2

        new_internal = BPlusTreeNode(is_leaf=False)
        new_internal.keys = node.keys[mid + 1:]
        new_internal.children = node.children[mid + 1:]

        separator_key = node.keys[mid]

        node.keys = node.keys[:mid]
        node.children = node.children[:mid + 1]

        new_offset = self.save_node(new_internal)
        self.save_node_at(node_offset, node)

        return new_offset, separator_key

    def search(self, id):
        offset = self.search_aux(self.root_offset, id)

        if offset is None:
            return None

        with open(self.filename, 'rb') as file:
            file.seek(offset)
            binary_record = file.read(RECORD_SIZE)
            return Record.from_bytes(binary_record)

    def search_aux(self, node_offset, id):
        node = self.load_node(node_offset)

        if node.is_leaf:
            for record in node.records:
                if record.key == id:
                    return record.offset
            return None

        else:
            idx = 0
            while idx < len(node.keys) and node.keys[idx] < id:
                idx += 1
            return self.search_aux(node.children[idx], id)
        
    def range_search(self, min, max):
        answers = []
        self.range_search_aux(self.root_offset, min, max, answers)

        if not answers:
            return None

        final_answer = []
        with open(self.filename, 'rb') as file:
            for offset in answers:
                file.seek(offset)
                binary_record = file.read(RECORD_SIZE)
                final_answer.append(Record.from_bytes(binary_record))

        return final_answer

    def range_search_aux(self, node_offset, min, max, vector):
        node = self.load_node(node_offset)

        if node.is_leaf:
            while node is not None:
                for record in node.records:
                    if min <= record.key <= max:
                        vector.append(record.offset)
                    elif record.key > max:
                        return
                if node.next:
                    node = self.load_node(node.next)
                else:
                    break
        else:
            idx = 0
            while idx < len(node.keys) and node.keys[idx] < min:
                idx += 1
            self.range_search_aux(node.children[idx], min, max, vector)
        