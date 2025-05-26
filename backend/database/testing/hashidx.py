import os
import sys
import time
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from database import *
import string

def _test_hashidx(n: int):
    table_name = f"Heap{n}"
    schema = [("id", "i"), ("nombre", "20s"), ("precio", "f")]

    # Crear tabla e índice hash sobre el campo "nombre"
    create_table(table_name, schema, primary_key="id")
    create_hash_idx(table_name, "nombre")
    print(f"Tabla {table_name} creada.")
    print(f"Índice hash sobre el campo 'nombre' creado.")

    nombre_objetivo = None

    print(f"== INSERTANDO {n} REGISTROS ==")
    for i in range(n):
        nombre = "P" + ''.join(random.choices(string.ascii_uppercase, k=5))
        if i == n // 2:
            nombre_objetivo = nombre
        precio = round(random.uniform(1.0, 100.0), 2)
        rec = Record(schema, [i + 1, nombre, precio])
        insert_record(table_name, rec)

    print(f"\nSe insertaron {n} registros en HeapFile '{table_name}'.")
    print(f"Buscando el nombre objetivo: {nombre_objetivo}\n")

    # Cronometrar búsqueda sin índice
    start = time.time()
    results = search_by_field(table_name, "nombre", nombre_objetivo)
    end = time.time()
    for r in results:
        print(r)
    print(f"\nBúsqueda sin índice tomó {end - start:.6f} segundos")

    # Cronometrar búsqueda con índice hash
    start = time.time()
    results = search_hash_idx(table_name, "nombre", nombre_objetivo)
    end = time.time()
    for r in results:
        print(r)
    print(f"Búsqueda con índice hash tomó {end - start:.6f} segundos")

