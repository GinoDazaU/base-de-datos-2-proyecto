#renato

class BPlusTreeIndex:
    
    def __init__(self, table_name: str, indexed_file: str):
        self.filename = table_name + "." + indexed_file + ".btree.idx"

import struct

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
        self.keys = []
        self.children = []  
        self.next = None   

class BPlusTree:
    def __init__(self, order, filename, auxname):
        self.order = order
        self.max_keys = order
        self.node_size = 16 + 4 * self.max_keys + 8 * (self.max_keys + 1)
        self.filename = filename
        self.auxname = auxname

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
        
        keys = list(struct.unpack(f'{self.max_keys}i', buffer[16:16 + 4 * self.max_keys]))

        if is_leaf:
            children = list(struct.unpack(f'{self.max_keys}Q', buffer[64:64 + 8 * self.max_keys]))
        else:
            children = list(struct.unpack(f'{self.max_keys + 1}Q', buffer[64:64 + 8 * (self.max_keys + 1)]))

        node = BPlusTreeNode(is_leaf=bool(is_leaf))
        node.keys = keys[:key_count]
        node.children = children[:key_count + (0 if is_leaf else 1)]
        node.next = next_leaf if is_leaf else None

        return node

    def save_node(self, node):
        is_leaf = int(node.is_leaf)
        key_count = len(node.keys)
        next_leaf = node.next if node.is_leaf else 0

        keys = node.keys + [0] * (self.max_keys - len(node.keys))

        if node.is_leaf:
            children = node.children + [0] * (self.max_keys - len(node.children))
        else:
            children = node.children + [0] * (self.max_keys + 1 - len(node.children))

        header = struct.pack('iiQ', is_leaf, key_count, next_leaf)
        key_data = struct.pack(f'{self.max_keys}i', *keys)

        if node.is_leaf:
            child_data = struct.pack(f'{self.max_keys}Q', *children)
        else:
            child_data = struct.pack(f'{self.max_keys + 1}Q', *children)

        buffer = header + key_data + child_data
        buffer += b'\x00' * (self.node_size - len(buffer))

        with open(self.auxname, 'ab') as f:
            pos = f.tell()
            f.write(buffer)
            return pos
        
    def save_node_at(self, offset, node):
        is_leaf = int(node.is_leaf)
        key_count = len(node.keys)
        next_leaf = node.next if node.is_leaf and node.next is not None else 0

        keys = node.keys + [0] * (self.max_keys - len(node.keys))

        if node.is_leaf:
            children = node.children + [0] * (self.max_keys - len(node.children))
        else:
            children = node.children + [0] * ((self.max_keys + 1) - len(node.children))

        header = struct.pack('iiQ', is_leaf, key_count, next_leaf)
        key_data = struct.pack(f'{self.max_keys}i', *keys)

        if node.is_leaf:
            child_data = struct.pack(f'{self.max_keys}Q', *children)
        else:
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
            file.write(Record.to_bytes(record))
            result = self._insert_aux(self.root_offset, record.id, pos)
            if result:
                new_node_offset, separator_key = result
                new_root = BPlusTreeNode(is_leaf=False)
                new_root.keys = [separator_key]
                new_root.children = [self.root_offset, new_node_offset]
                new_root_offset = self.save_node(new_root)
                self.update_root_offset(new_root_offset)

    def _insert_aux(self, node_offset, key, offset):
        node = self.load_node(node_offset)
        if node.is_leaf:
            idx = 0
            while idx < len(node.keys) and key > node.keys[idx]:
                idx += 1
            node.keys.insert(idx, key)
            node.children.insert(idx, offset)

            if len(node.keys) > self.order:
                return self._split_leaf(node, node_offset)
            else:
                self.save_node_at(node_offset, node)  
                return None
        else:
            idx = 0
            while idx < len(node.keys) and key > node.keys[idx]:
                idx += 1
            result = self._insert_aux(node.children[idx], key, offset)
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
        mid = len(node.keys) // 2

        new_leaf = BPlusTreeNode(is_leaf=True)
        new_leaf.keys = node.keys[mid:]
        new_leaf.children = node.children[mid:]
        new_leaf.next = node.next

        node.keys = node.keys[:mid]
        node.children = node.children[:mid]
        node.next = self.save_node(new_leaf) 

        new_leaf_offset = node.next
        self.save_node_at(node_offset, node) 

        return new_leaf_offset, new_leaf.keys[0] 

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

#----------------------------------------------------------------------------------------