import os
import sys
import time
import string
import random

# Añadir el directorio padre al sys.path para importar módulos
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Importar funciones y clases necesarias de database y storage
# Asegúrate de que 'database' y 'storage.Record' sean accesibles desde el path
from database import create_table_with_btree_pk, create_seq_idx, create_hash_idx, create_btree_idx, insert_record_btree_pk, search_hash_idx, search_by_field, search_seq_idx_range, search_btree_idx
from storage.Record import Record

def test_create_student_table_with_data(n=10):
    """
    Crea una tabla 'alumnos' con índices sobre campos clave, incluyendo
    múltiples índices para el campo 'codigo' (hash, btree, secuencial).
    Genera n registros aleatorios para pruebas y guarda los tiempos en resultados_test.txt.
    """
    table_name = "alumnos10k"
    schema = [
        ("codigo", "i"),          # Clave primaria (original)
        ("nombre", "20s"),        # Nombre
        ("pension", "f"),         # Pensión mensual
        ("ciclo", "i"),           # Ciclo actual
        ("especialidad", "15s"),  # Carrera
        ("codigo_hash", "i"),     # Nuevo campo para índice hash
        ("codigo_btree", "i"),    # Nuevo campo para índice btree
        ("codigo_seq", "i"),      # Nuevo campo para índice secuencial
    ]
    primary_key = "codigo"

    # Preparar tabla e índices
    create_table_with_btree_pk(table_name, schema, primary_key)
    create_seq_idx(table_name, "pension")
    create_hash_idx(table_name, "nombre")
    create_btree_idx(table_name, "ciclo")

    # Crear índices para los nuevos campos de código
    create_hash_idx(table_name, "codigo_hash")
    create_btree_idx(table_name, "codigo_btree")
    create_seq_idx(table_name, "codigo_seq") # Nota: un índice secuencial para un campo numérico exacto no es común, pero se añade según la petición.

    nombres = ["Ana", "Luis", "Carlos", "María", "Elena", "Jorge", "Lucía", "Pedro", "Sofía", "Diego"]
    carreras = ["Sistemas", "Industrial", "Civil", "Ambiental", "Mecánica", "Contabilidad"]

    codigos_usados = set()
    start_time = time.time()

    for _ in range(n):
        while True:
            codigo = random.randint(10000, 99999)
            if codigo not in codigos_usados:
                codigos_usados.add(codigo)
                break

        nombre = random.choice(nombres)
        pension = round(random.uniform(300.0, 1500.0), 2)
        ciclo = random.randint(1, 10)
        especialidad = random.choice(carreras)

        # Crear el registro, duplicando el valor de 'codigo' en los nuevos campos
        record = Record(schema, [
            codigo,
            nombre,
            pension,
            ciclo,
            especialidad,
            codigo, # codigo_hash
            codigo, # codigo_btree
            codigo  # codigo_seq
        ])
        insert_record_btree_pk(table_name, record)

    end_time = time.time()
    elapsed = end_time - start_time

    print(f"✅ Insertados {n} alumnos en la tabla '{table_name}'.")

    # Guardar en archivo
    with open("resultados_test.txt", "a", encoding="utf-8") as f:
        f.write(f"🔢 Insertados {n} registros con índices (btree + hash + seq) en {elapsed:.4f} segundos.\n\n")


def test_search_comparison(n):
    """
    Compara el rendimiento de diferentes tipos de búsquedas (con y sin índices)
    en la tabla 'alumnos'.
    """
    table_name = "alumnos"

    test_nombre = "Luis"
    test_pension_min, test_pension_max = 500.0, 1000.0
    test_ciclo = 5

    # Seleccionar un código aleatorio existente para la prueba de búsqueda por código
    # Esto asume que la tabla ya tiene datos.
    all_records = search_by_field(table_name, "codigo", None) # Obtener todos los registros para elegir un código
    if not all_records:
        print("No hay registros para buscar. Ejecuta test_create_student_table_with_data primero.")
        return
    test_codigo = random.choice(all_records).values[0] # Elige un código de un registro existente

    resultados = []
    resultados.append(f"🔍 Comparando búsquedas con {n} registros en la tabla '{table_name}':\n")

    # Búsqueda por Nombre: Hash vs Secuencial
    t0 = time.time()
    result_hash_nombre = search_hash_idx(table_name, "nombre", test_nombre)
    t1 = time.time()
    result_seq_nombre = search_by_field(table_name, "nombre", test_nombre)
    t2 = time.time()
    resultados.append(f"🔸 Nombre = '{test_nombre}'")
    resultados.append(f"Hash Index (nombre)    → {len(result_hash_nombre)} resultados en {t1 - t0:.6f} s")
    resultados.append(f"Búsqueda Lineal (nombre)→ {len(result_seq_nombre)} resultados en {t2 - t1:.6f} s\n")

    # Búsqueda por Pensión: secuencial sin índice vs con índice de rango
    t0 = time.time()
    # Para el heap scan, necesitamos iterar sobre todos los registros y filtrar manualmente
    schema_pension_idx = [name for name, _ in all_records[0].schema].index("pension")
    result_heap_pension = [r for r in all_records if test_pension_min <= r.values[schema_pension_idx] <= test_pension_max]
    t1 = time.time()
    result_seq_idx_pension = search_seq_idx_range(table_name, "pension", test_pension_min, test_pension_max)
    t2 = time.time()
    resultados.append(f"🔸 Pensión en rango [{test_pension_min}, {test_pension_max}]")
    resultados.append(f"Heap Scan (pension)    → {len(result_heap_pension)} resultados en {t1 - t0:.6f} s")
    resultados.append(f"SequentialIdx (pension)→ {len(result_seq_idx_pension)} resultados en {t2 - t1:.6f} s\n")

    # Búsqueda por Ciclo: B+Tree vs Secuencial
    t0 = time.time()
    result_btree_ciclo = search_btree_idx(table_name, "ciclo", test_ciclo)
    t1 = time.time()
    result_seq_ciclo = search_by_field(table_name, "ciclo", test_ciclo)
    t2 = time.time()
    resultados.append(f"🔸 Ciclo = {test_ciclo}")
    resultados.append(f"B+Tree Index (ciclo)   → {len(result_btree_ciclo)} resultados en {t1 - t0:.6f} s")
    resultados.append(f"Búsqueda Lineal (ciclo)→ {len(result_seq_ciclo)} resultados en {t2 - t1:.6f} s\n")

    # --- Nuevas comparaciones para los campos 'codigo' ---

    # Búsqueda por Codigo (PK B+Tree) vs Hash vs B+Tree vs Secuencial
    t0 = time.time()
    # Asumiendo que la PK 'codigo' usa B+Tree internamente para búsqueda rápida
    result_pk_codigo = search_btree_idx(table_name, "codigo", test_codigo) # O la función de búsqueda de PK si es diferente
    t1 = time.time()
    result_hash_codigo = search_hash_idx(table_name, "codigo_hash", test_codigo)
    t2 = time.time()
    result_btree_codigo = search_btree_idx(table_name, "codigo_btree", test_codigo)
    t3 = time.time()
    result_seq_codigo_idx = search_seq_idx_range(table_name, "codigo_seq", test_codigo, test_codigo) # Rango para búsqueda exacta en índice secuencial
    t4 = time.time()
    result_linear_codigo = search_by_field(table_name, "codigo", test_codigo)
    t5 = time.time()

    resultados.append(f"🔸 Código = {test_codigo}")
    resultados.append(f"PK B+Tree (codigo)     → {len(result_pk_codigo)} resultados en {t1 - t0:.6f} s")
    resultados.append(f"Hash Index (codigo_hash)→ {len(result_hash_codigo)} resultados en {t2 - t1:.6f} s")
    resultados.append(f"B+Tree Index (codigo_btree)→ {len(result_btree_codigo)} resultados en {t3 - t2:.6f} s")
    resultados.append(f"SequentialIdx (codigo_seq)→ {len(result_seq_codigo_idx)} resultados en {t4 - t3:.6f} s")
    resultados.append(f"Búsqueda Lineal (codigo)→ {len(result_linear_codigo)} resultados en {t5 - t4:.6f} s\n")


    print("\n".join(resultados))

    with open("resultados_test.txt", "a", encoding="utf-8") as f:
        f.write("\n".join(resultados))
        f.write("\n" + "="*60 + "\n\n")


if __name__ == "__main__":
    n = 10000 # Número de registros para probar
    test_create_student_table_with_data(n)
    test_search_comparison(n)
