import os
import sys
import time
import random
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from database import *

def _test_rtreeidx(n: int):
    table_name = "RTreeTest"
    schema = [("id", "i"), ("coord", "2f")]
    create_table(table_name, schema, primary_key="id")

    print(f"Test RTree Index with {n} records")

    for i in range(1, n + 1):
        record = Record(schema, [int(i), (random.uniform(-100, 100), random.uniform(-100, 100))])
        insert_record(table_name, record)
    pass

    create_rtree_idx(table_name, "coord")
    print(f"RTree index created for {table_name} on 'coord' field.")

if __name__ == "__main__":
    _test_rtreeidx(1)