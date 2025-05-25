from database import *
import random
import string
import glob
import os
import time

def _table_path(table_name: str) -> str:
    """Devuelve la ruta absoluta (sin extensión) de la tabla."""
    return os.path.join(tables_dir, table_name)

def _demo_heap_seqidx_insert_1000():
    """Demo: crea un HeapFile e inserta 1000 registros (sin índices)."""

    table_name = "Heap1000"
    schema = [("id", "i"), ("nombre", "20s"), ("precio", "f")]

    # Eliminar archivos anteriores
    if os.path.exists(_table_path(table_name) + ".dat"):
        for f in glob.glob(_table_path(table_name) + ".*"):
            os.remove(f)

    # Crear tabla e índice
    create_table(table_name, schema, primary_key="id")
    create_seq_idx(table_name, schema[1][0])  # índice sobre el campo "nombre"

    # Insertar 1000 registros y guardar un nombre para búsqueda
    nombre_objetivo = None
    for i in range(1000):
        nombre = "P" + ''.join(random.choices(string.ascii_uppercase, k=5))
        if i == 523:  # Elegimos un nombre arbitrario
            nombre_objetivo = nombre
        precio = round(random.uniform(1.0, 100.0), 2)
        rec = Record(schema, [i + 1, nombre, precio])
        insert_record(table_name, rec)

    print("\nSe insertaron 1000 registros en HeapFile 'Heap1000'.")
    print("Se insertaron 1000 registros en el índice secuencial.")

    print_table(table_name)
    print_seq_idx(table_name, schema[1][0])

    print(f"\nBuscando el nombre objetivo: {nombre_objetivo}")

    # Cronometrar búsqueda sin índice
    start = time.time()
    results: list[Record] = search_by_field(table_name, schema[1][0], nombre_objetivo)
    for r in results:
        r.print()
    end = time.time()
    print(f"Búsqueda sin índice tomó {end - start:.6f} segundos")

    # Cronometrar búsqueda con índice
    start = time.time()
    search_seq_idx(table_name, schema[1][0], nombre_objetivo)
    end = time.time()
    print(f"Búsqueda con índice secuencial tomó {end - start:.6f} segundos")


def _demo_heap_hashidx_insert_1000():
    """Demo: crea un HeapFile e inserta 1000 registros (sin índices)."""

    table_name = "Heap1000"
    schema = [("id", "i"), ("nombre", "20s"), ("precio", "f")]

    # Eliminar archivos anteriores
    if os.path.exists(_table_path(table_name) + ".dat"):
        for f in glob.glob(_table_path(table_name) + ".*"):
            os.remove(f)

    # Crear tabla e índice
    create_table(table_name, schema, primary_key="id")
    create_hash_idx(table_name, schema[1][0])  # índice sobre el campo "nombre"

    # Insertar 1000 registros y guardar un nombre para búsqueda
    nombre_objetivo = None
    for i in range(1000):
        nombre = "P" + ''.join(random.choices(string.ascii_uppercase, k=5))
        if i == 523:  # Elegimos un nombre arbitrario
            nombre_objetivo = nombre
        precio = round(random.uniform(1.0, 100.0), 2)
        rec = Record(schema, [i + 1, nombre, precio])
        insert_record(table_name, rec)

    print("\nSe insertaron 1000 registros en HeapFile 'Heap1000'.")
    print("Se insertaron 1000 registros en el índice secuencial.")

    print_table(table_name)
    print_hash_idx(table_name)

    print(f"\nBuscando el nombre objetivo: {nombre_objetivo}")

    # Cronometrar búsqueda sin índice
    start = time.time()
    results: list[Record] = search_by_field(table_name, schema[1][0], nombre_objetivo)
    for r in results:
        r.print()
    end = time.time()
    print(f"Búsqueda sin índice tomó {end - start:.6f} segundos")

    # Cronometrar búsqueda con índice
    start = time.time()
    search_hash_idx(table_name, schema[1][0], nombre_objetivo)
    end = time.time()
    print(f"Búsqueda con índice secuencial tomó {end - start:.6f} segundos")

if __name__ == "__main__":
    _demo_heap_hashidx_insert_1000()
