#renato

class BPlusTreeIndex:
    
    def __init__(self, table_name: str, indexed_file: str):
        self.filename = table_name + "." + indexed_file + ".btree.idx"
