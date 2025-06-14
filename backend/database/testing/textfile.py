import os
import sys
import time
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from database import *

if __name__ == "__main__":
    table_name = "textfile"
    schema = [("id", "i"), ("titulo", "text"), ("contenido", "text")]

    create_table(table_name, schema, primary_key="id")

    r1 = Record(schema, [2, "noticia1", "asd"])
    r2 = Record(schema, [3, "noticia1", "asdasd"])
    r3 = Record(schema, [4, "noticia1", "asdasdasd"])

    records = [r1, r2, r3]

    for r in records:
        insert_record(table_name, r)
