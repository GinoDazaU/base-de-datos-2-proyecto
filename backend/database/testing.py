from database import *
import random
import string
import glob
import os
import time
from faker import Faker

def _table_path(table_name: str) -> str:
    """Devuelve la ruta absoluta (sin extensión) de la tabla."""
    return os.path.join(tables_dir, table_name)

def _test_heapfile(n: int):
    fake = Faker()

    table_name = "Alumno"
    schema = [("codigo", "10s"), ("nombre", "20s"), ("precio", "f")]
    pk = "codigo"

    # Limpiar archivos existentes
    for path in glob.glob(f"{_table_path(table_name)}*"):
        os.remove(path)

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


def _test_seqidx(n: int):
    fake = Faker()

    table_name = "Alumno"
    schema = [("codigo", "10s"), ("nombre", "20s"), ("precio", "f")]
    pk = "codigo"

    for path in glob.glob(f"{_table_path(table_name)}*"):
        os.remove(path)

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


def _test_hashidx():
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
    for i in range(10000):
        nombre = "P" + ''.join(random.choices(string.ascii_uppercase, k=5))
        if i == 5223:  # Elegimos un nombre arbitrario
            nombre_objetivo = nombre
        precio = round(random.uniform(1.0, 100.0), 2)
        rec = Record(schema, [i + 1, nombre, precio])
        insert_record(table_name, rec)

    print("\nSe insertaron 1000 registros en HeapFile 'Heap1000'.")
    print("Se insertaron 1000 registros en el índice hash.")

    print_table(table_name)

    print(f"\nBuscando el nombre objetivo: {nombre_objetivo}")

    # Cronometrar búsqueda sin índice
    start = time.time()
    results: list[Record] = search_by_field(table_name, schema[1][0], nombre_objetivo)
    for r in results:
        print(r)
    end = time.time()
    print(f"Búsqueda sin índice tomó {end - start:.6f} segundos")

    # Cronometrar búsqueda con índice
    start = time.time()
    results = search_hash_idx(table_name, schema[1][0], nombre_objetivo)
    end = time.time()
    for r in results:
        print(r)
    print(f"Búsqueda con índice hash tomó {end - start:.6f} segundos")

def _test_insercion_sin_pk():
    schema = [("id", "i"), ("nombre", "20s"), ("precio", "f")]
    registros = 4000

    # Limpiar archivos anteriores
    for f in glob.glob(_table_path("SinPk") + ".*"):
        os.remove(f)

    # Crear tabla con PK, pero sin usar su restricción
    create_table("SinPk", schema, primary_key="id")

    heap = HeapFile(_table_path("SinPk"))

    tiempo_inicio = time.time()
    for i in range(registros):
        nombre = "P" + ''.join(random.choices(string.ascii_uppercase, k=5))
        precio = round(random.uniform(1.0, 100.0), 2)
        rec = Record(schema, [i + 1, nombre, precio])
        heap.insert_record_free(rec)
    tiempo_total = time.time() - tiempo_inicio

    print(f"Tiempo de inserción sin verificación de PK: {tiempo_total:.4f} segundos")

if __name__ == "__main__":
    _test_seqidx(1000)