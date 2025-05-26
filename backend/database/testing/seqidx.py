import os
import sys
import time
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from database import *
from faker import Faker

def _test_seqidx(n: int):
    fake = Faker()

    table_name = "seqidx_test"
    schema = [("codigo", "10s"), ("nombre", "20s"), ("precio", "f")]
    pk = "codigo"

    create_table(table_name, schema, pk)
    create_seq_idx(table_name, "codigo")  # índice secuencial por código

    target_index = n // 2
    target_codigo = f"A{target_index:05d}"

    print(f"== INSERTANDO {n} REGISTROS ==")
    for i in range(n):
        codigo = f"A{i:05d}"
        nombre = fake.first_name()
        precio = round(random.uniform(1.0, 100.0), 2)
        rec = Record(schema, [codigo, nombre, precio])
        insert_record(table_name, rec)

    print(f"== BUSCANDO {target_codigo} ==")

    t1 = time.time()
    resultados = search_by_field(table_name, "codigo", target_codigo)
    t2 = time.time()
    print(f"Sin índice: {'ENCONTRADO' if resultados else 'NO ENCONTRADO'} en {t2 - t1:.6f} segundos")
    for r in resultados:
        print(r)

    t3 = time.time()
    resultados = search_seq_idx(table_name, "codigo", target_codigo)
    t4 = time.time()
    print(f"Con índice secuencial: {t4 - t3:.6f} segundos")
    for r in resultados:
        print(r)

    print("== BORRANDO ==")
    delete_record(table_name, target_codigo)

    print("== BUSCANDO POST-BORRADO ==")
    print("== BUSCANDO SIN INDICE ==")
    resultados = search_by_field(table_name, "codigo", target_codigo)
    print(f"Buscar {target_codigo} después de borrar: {'ENCONTRADO' if resultados else 'NO ENCONTRADO'}")
    print("== BUSCANDO CON INDICE SECUENCIAL ==")
    resultados = search_seq_idx(table_name, "codigo", target_codigo)
    print(f"Buscar {target_codigo} después de borrar: {'ENCONTRADO' if resultados else 'NO ENCONTRADO'}")

if __name__ == "__main__":
    _test_seqidx(1000)