import os
import struct
import json

class Record:
    def __init__(self, schema, values=None):
        self.schema = schema
        self.names = [name for name, _ in schema]
        self.formats = [fmt for _, fmt in schema]
        self.struct = struct.Struct(''.join(self.formats))
        self.values = values if values is not None else [None] * len(self.names)

    def pack(self):
        packed = []
        for (name, fmt), val in zip(self.schema, self.values):
            if fmt.endswith('s'):
                size = int(fmt[:-1])
                raw = val.encode('utf-8') if isinstance(val, str) else val
                raw = raw[:size].ljust(size, b'\x00')
                packed.append(raw)
            else:
                packed.append(val)
        return self.struct.pack(*packed)

    @classmethod
    def unpack(cls, schema, data):
        st = struct.Struct(''.join(fmt for _, fmt in schema))
        unpacked = st.unpack(data)
        values = []
        for (name, fmt), val in zip(schema, unpacked):
            if fmt.endswith('s'):
                values.append(val.rstrip(b'\x00').decode('utf-8'))
            else:
                values.append(val)
        return cls(schema, values)

    def __repr__(self):
        pairs = [f"{n}={v!r}" for n, v in zip(self.names, self.values)]
        return f"<Record {' '.join(pairs)}>"


def build_table(table_name, schema, key_field, block_factor):
    data_file = f"{table_name}.data.dat"
    index1_file = f"{table_name}.index1.dat"
    index2_file = f"{table_name}.index2.dat"
    overflow_file = f"{table_name}.overflow.dat"
    meta_file = f"{table_name}.isam.meta.json"

    for f in [data_file, index1_file, index2_file, overflow_file, meta_file]:
        try:
            os.remove(f)
        except OSError:
            pass

    with open(data_file, 'wb') as df:
        df.write(struct.pack('i', 0))

    open(index1_file, 'wb').close()
    open(index2_file, 'wb').close()
    open(overflow_file, 'wb').close()

    meta = {
        'schema': schema,
        'key_field': key_field,
        'block_factor': block_factor,
        'record_count': 0,
        'root': [{'max_key': None, 'leaf_id': 0}],
        'leaves': {0: []},
        'overflow_heads': {},
        'overflow_list': []
    }
    with open(meta_file, 'w') as mf:
        json.dump(meta, mf, indent=4)

class ISAM:
    def __init__(self, table_name, key_field, block_factor):
        self.table_name = table_name
        self.data_file = f"{table_name}.data.dat"
        self.index1_file = f"{table_name}.index1.dat"
        self.index2_file = f"{table_name}.index2.dat"
        self.overflow_file = f"{table_name}.overflow.dat"
        self.meta_file = f"{table_name}.isam.meta.json"

        with open(self.meta_file, 'r') as mf:
            self.meta = json.load(mf)

        self.schema = self.meta['schema']
        self.names = [n for n, _ in self.schema]
        self.key_field = self.meta['key_field']
        self.key_index = self.names.index(self.key_field)
        self.block_factor = self.meta['block_factor']
        self.record_struct = struct.Struct(''.join(fmt for _, fmt in self.schema))
        self.record_size = self.record_struct.size

        self.record_count = self.meta['record_count']
        self.leaves = {int(k): v for k, v in self.meta['leaves'].items()}
        self.root = self.meta['root']
        self.overflow_heads = {int(k): v for k, v in self.meta['overflow_heads'].items()}
        self.overflow_list = self.meta['overflow_list']

    def save_meta(self):
        self.meta['record_count'] = self.record_count
        self.meta['root'] = self.root
        self.meta['leaves'] = self.leaves
        self.meta['overflow_heads'] = self.overflow_heads
        self.meta['overflow_list'] = self.overflow_list
        with open(self.meta_file, 'w') as mf:
            json.dump(self.meta, mf, indent=4)

    def build_index(self):
        pairs = []
        for rec_num in range(self.record_count):
            rec = self.fetch(rec_num)
            key = rec.values[self.key_index]
            pairs.append((key, rec_num))
        pairs.sort(key=lambda x: x[0])

        if not pairs:
            self.leaves = {0: []}
            self.root = [{'max_key': None, 'leaf_id': 0}]
        else:
            self.leaves = {}
            self.root = []
            for i in range((len(pairs) + self.block_factor - 1) // self.block_factor):
                chunk = pairs[i * self.block_factor:(i + 1) * self.block_factor]
                self.leaves[i] = chunk
                max_key = chunk[-1][0]
                self.root.append({'max_key': max_key, 'leaf_id': i})

        self.overflow_heads = {}
        self.overflow_list = []
        self.save_meta()

    def _find_leaf(self, key):
        for entry in self.root:
            if entry['max_key'] is None or key <= entry['max_key']:
                return entry['leaf_id']
        return self.root[-1]['leaf_id']

    def add(self, record):
        with open(self.data_file, 'r+b') as df:
            df.seek(0)
            df.write(struct.pack('i', self.record_count + 1))
            df.seek(0, 2)
            df.write(record.pack())
        rec_num = self.record_count
        self.record_count += 1

        key = record.values[self.key_index]
        leaf_id = self._find_leaf(key)
        block = self.leaves.get(leaf_id, [])
        if len(block) < self.block_factor:
            block.append((key, rec_num))
            block.sort(key=lambda x: x[0])
            self.leaves[leaf_id] = block
        else:
            head = self.overflow_heads.get(leaf_id)
            entry = {'leaf_id': leaf_id, 'key': key, 'rec_num': rec_num, 'next': head, 'removed': False}
            idx = len(self.overflow_list)
            self.overflow_list.append(entry)
            self.overflow_heads[leaf_id] = idx

        for entry in self.root:
            if entry['leaf_id'] == leaf_id:
                blk = self.leaves.get(leaf_id, [])
                entry['max_key'] = blk[-1][0] if blk else None
                break

        self.save_meta()

    def fetch(self, rec_num):
        with open(self.data_file, 'rb') as df:
            df.seek(4 + rec_num * self.record_size)
            data = df.read(self.record_size)
        return Record.unpack(self.schema, data)

    def search(self, key):
        results = []
        leaf_id = self._find_leaf(key)
        for k, rnum in self.leaves.get(leaf_id, []):
            if k == key:
                results.append(self.fetch(rnum))
        idx = self.overflow_heads.get(leaf_id)
        while idx is not None:
            entry = self.overflow_list[idx]
            if not entry['removed'] and entry['key'] == key:
                results.append(self.fetch(entry['rec_num']))
            idx = entry['next']
        return results

    def rangeSearch(self, begin_key, end_key):
        results = []
        sorted_root = sorted(self.root, key=lambda e: (e['max_key'] is not None, e['max_key'] or 0))
        for entry in sorted_root:
            lid = entry['leaf_id']
            for k, rnum in self.leaves.get(lid, []):
                if begin_key <= k <= end_key:
                    results.append(self.fetch(rnum))
            idx = self.overflow_heads.get(lid)
            while idx is not None:
                e = self.overflow_list[idx]
                if not e['removed'] and begin_key <= e['key'] <= end_key:
                    results.append(self.fetch(e['rec_num']))
                idx = e['next']
        return results

    def remove(self, key):
        leaf_id = self._find_leaf(key)
        block = self.leaves.get(leaf_id, [])
        self.leaves[leaf_id] = [(k, r) for k, r in block if k != key]
        idx = self.overflow_heads.get(leaf_id)
        while idx is not None:
            entry = self.overflow_list[idx]
            if not entry['removed'] and entry['key'] == key:
                entry['removed'] = True
            idx = entry['next']
        for entry in self.root:
            if entry['leaf_id'] == leaf_id:
                blk = self.leaves.get(leaf_id, [])
                entry['max_key'] = blk[-1][0] if blk else None
                break
        self.save_meta()

    def print_index(self):
        print("Root:", self.root)
        print("Leaves:", self.leaves)
        print("Overflow Heads:", self.overflow_heads)
        print("Overflow List:", [e for e in self.overflow_list if not e['removed']])


def test():
    for f in ["test.data.dat", "test.index1.dat", "test.index2.dat", "test.overflow.dat", "test.isam.meta.json"]:
        try: os.remove(f)
        except: pass

    schema = [("id", "i"), ("nombre", "20s"), ("precio", "f"), ("cantidad", "i")]
    build_table("test", schema, "id", block_factor=2)
    isam = ISAM("test", "id", 2)
    isam.build_index()

    # Inserciones para overflow
    for vals in [(1, "Apple", 0.5, 10), (2, "Banana", 0.3, 20), (3, "Cherry", 0.2, 30)]:
        isam.add(Record(schema, list(vals)))

    print("Search id=3:", isam.search(3))
    print("Range 1-3:", isam.rangeSearch(1, 3))
    isam.remove(2)
    print("After removal id=2:", isam.search(2))
    isam.print_index()

if __name__ == "__main__":
    test()
