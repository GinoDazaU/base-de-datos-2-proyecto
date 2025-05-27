import os
import sys
import time
import string
import random

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from database import *
from storage.Record import Record

def _test_btreeidx(n: int):
    table_name = f"Heap{n}"
    schema = [("id", "i"), ("nombre", "20s"), ("precio", "f")]

    # Crear tabla y crear índice B+ en el campo 'nombre'
    create_table(table_name, schema, primary_key="id")
    create_btree_idx(table_name, "nombre")
    print(f"Tabla '{table_name}' creada con índice B+ en 'nombre'.")

    nombre_objetivo = None

    print(f"== INSERTANDO {n} REGISTROS ==")
    for i in range(n):
        nombre = "P" + ''.join(random.choices(string.ascii_uppercase, k=5))
        if i == n // 2:
            nombre_objetivo = nombre
        precio = round(random.uniform(1.0, 100.0), 2)
        rec = Record(schema, [i + 1, nombre, precio])
        insert_record(table_name, rec)

    print(f"\nBuscando registros con nombre: {nombre_objetivo}\n")

    # Búsqueda sin índice
    t1 = time.time()
    res_no_idx = search_by_field(table_name, "nombre", nombre_objetivo)
    t2 = time.time()
    print(f"Sin índice: {len(res_no_idx)} encontrado(s) en {t2 - t1:.6f} s")

    # Búsqueda con índice B+
    t3 = time.time()
    res_btree_idx = search_btree_idx(table_name, "nombre", nombre_objetivo)
    t4 = time.time()
    print(f"Con índice B+: {len(res_btree_idx)} encontrado(s) en {t4 - t3:.6f} s")

    # Eliminación por PK de todos los encontrados
    print("\n== ELIMINANDO REGISTROS POR PK ==")
    for r in res_no_idx:
        pk_idx = [i for i, (n, _) in enumerate(r.schema) if n == "id"][0]
        delete_record(table_name, r.values[pk_idx])

    # Verificación post-borrado
    print(f"\n== VERIFICACIÓN POST-BORRADO de {nombre_objetivo} ==")
    res1 = search_by_field(table_name, "nombre", nombre_objetivo)
    print(f"Sin índice: {'ENCONTRADO' if res1 else 'NO ENCONTRADO'}")

    res2 = search_btree_idx(table_name, "nombre", nombre_objetivo)
    print(f"Con índice B+: {'ENCONTRADO' if res2 else 'NO ENCONTRADO'}")

    # Elegimos valores de rango basados en el alfabeto
    valor_inicio = "PA"    # por ejemplo
    valor_fin = "PZ"

    print(f"\n== BÚSQUEDA POR RANGO: '{valor_inicio}' a '{valor_fin}' ==")
    t5 = time.time()
    res_rango = search_btree_idx_range(table_name, "nombre", valor_inicio, valor_fin)
    t6 = time.time()
    print(f"Con índice B+ (rango): {len(res_rango)} encontrado(s) en {t6 - t5:.6f} s")

    print("\n== SCAN B+ TREE ==")
    #print_btree_idx(table_name, "nombre")

def _test_btreeidx_integers(n: int):
    table_name = f"HeapInt{n}"
    schema = [("id", "i"), ("codigo", "i"), ("precio", "f")]

    create_table(table_name, schema, primary_key="id")
    create_btree_idx(table_name, "codigo")
    print(f"Tabla '{table_name}' creada con índice B+ en 'codigo'.")

    codigo_objetivo = None

    print(f"== INSERTANDO {n} REGISTROS ==")
    for i in range(n):
        codigo = random.randint(1000, 9999)
        if i == n // 2:
            codigo_objetivo = codigo
        precio = round(random.uniform(1.0, 100.0), 2)
        rec = Record(schema, [i + 1, codigo, precio])
        insert_record(table_name, rec)

    print(f"\nBuscando registros con codigo: {codigo_objetivo}\n")

    # Búsqueda sin índice
    t1 = time.time()
    res_no_idx = search_by_field(table_name, "codigo", codigo_objetivo)
    t2 = time.time()
    print(f"Sin índice: {len(res_no_idx)} encontrado(s) en {t2 - t1:.6f} s")

    # Búsqueda con índice B+
    t3 = time.time()
    res_btree_idx = search_btree_idx(table_name, "codigo", codigo_objetivo)
    t4 = time.time()
    print(f"Con índice B+: {len(res_btree_idx)} encontrado(s) en {t4 - t3:.6f} s")

    # Eliminación por PK de todos los encontrados
    print("\n== ELIMINANDO REGISTROS POR PK ==")
    for r in res_no_idx:
        pk_idx = [i for i, (n, _) in enumerate(r.schema) if n == "id"][0]
        delete_record(table_name, r.values[pk_idx])

    # Verificación post-borrado
    print(f"\n== VERIFICACIÓN POST-BORRADO de {codigo_objetivo} ==")
    res1 = search_by_field(table_name, "codigo", codigo_objetivo)
    print(f"Sin índice: {'ENCONTRADO' if res1 else 'NO ENCONTRADO'}")

    res2 = search_btree_idx(table_name, "codigo", codigo_objetivo)
    print(f"Con índice B+: {'ENCONTRADO' if res2 else 'NO ENCONTRADO'}")

if __name__ == "__main__":
    _test_btreeidx(100)
    #_test_btreeidx_integers(100)