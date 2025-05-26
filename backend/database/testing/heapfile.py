import os
import sys
import time
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from database import *
from faker import Faker

def _test_heapfile(n: int):
    fake = Faker()

    table_name = "heapfile_test"
    schema = [("codigo", "10s"), ("nombre", "20s"), ("precio", "f")]
    pk = "codigo"

    create_table(table_name, schema, pk)

    target_index = n // 2
    target_codigo = f"A{target_index:05d}"

    print(f"== INSERTANDO {n} REGISTROS ==")
    for i in range(n):
        codigo = f"A{i:05d}"
        nombre = fake.first_name()
        precio = round(fake.pyfloat(min_value=1.0, max_value=100.0), 2)
        rec = Record(schema, [codigo, nombre, precio])
        insert_record(table_name, rec)

    print("== BUSCANDO ==")
    t1 = time.time()
    resultados = search_by_field(table_name, "codigo", target_codigo)
    t2 = time.time()
    print(f"Buscar {target_codigo}: {'ENCONTRADO' if resultados else 'NO ENCONTRADO'} en {t2 - t1:.6f} segundos")
    for r in resultados:
        print(r)

    print("== BORRANDO ==")
    delete_record(table_name, target_codigo)

    print("== BUSCANDO POST-BORRADO ==")
    resultados = search_by_field(table_name, "codigo", target_codigo)
    print(f"Buscar {target_codigo}: {'ENCONTRADO' if resultados else 'NO ENCONTRADO'}")

if __name__ == "__main__":
    _test_heapfile(1000)