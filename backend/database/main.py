import os
import time
import random
from faker import Faker

from storage.HeapFile import HeapFile
from storage.Record import Record
from indexing.SequentialIndex import SequentialIndex

# Ruta de tablas
dir_actual = os.path.dirname(os.path.abspath(__file__))
TABLES_DIR = os.path.join(dir_actual, 'tables')
if not os.path.exists(TABLES_DIR):
    os.makedirs(TABLES_DIR)

# Configuración
TABLE_NAME = 'test_heap'
HEAP_FILE = os.path.join(TABLES_DIR, f'{TABLE_NAME}.dat')
SCHEMA = [
    ('id', 'i'),
    ('name', '20s'),
]
RECORD_COUNT = 50
RANDOM_ID_RANGE = (0, RECORD_COUNT * 2)  # Permitir duplicados


def main():
    fake = Faker()
    # 1. Construir heap file
    if os.path.exists(HEAP_FILE):
        os.remove(HEAP_FILE)
    print(f"Creando heap file con {RECORD_COUNT} registros...")
    HeapFile.build_file(HEAP_FILE, SCHEMA)
    heap = HeapFile(HEAP_FILE)

    # 2. Insertar registros con IDs aleatorios
    start = time.time()
    for _ in range(RECORD_COUNT):
        # Generar ID aleatorio (posibles duplicados)
        rand_id = random.randint(*RANDOM_ID_RANGE)
        # Generar nombre fijo de 20 caracteres
        nombre = fake.name()[:20].ljust(20)
        record = Record(heap.schema, [rand_id, nombre])
        heap.insert_record(record)
    end = time.time()
    print(f"Inserción completada en {end - start:.2f} segundos.")

    # 3. Construir índice secuencial sobre 'id'
    print("Construyendo índice secuencial sobre 'id'...")
    start = time.time()
    idx = SequentialIndex.build_index(HEAP_FILE, heap.extract_index)
    end = time.time()
    print(f"Índice '.seq.idx' creado en {end - start:.2f} segundos.")

    # 4. Prueba de búsqueda
    test_key = random.randint(*RANDOM_ID_RANGE)
    print(f"Buscando registro con key={test_key} en el índice...")
    rec = idx.search_record(test_key)
    if rec:
        print(f"Registro encontrado en índice: key={rec.key}, offset={rec.offset}")
    else:
        print("Registro no encontrado en índice.")

    # 5. Mostrar estado del índice
    print("Estado del índice (load):")
    idx.load()

    heap.load()
    print(f"Mostrando Registro {rec.key}:")
    test = heap.fetch_by_offset(rec.offset)
    test.print()
    

    # 6. Limpiar (opcional)
    # os.remove(HEAP_FILE)
    # os.remove(HEAP_FILE.replace('.dat', '.seq.idx'))


if __name__ == '__main__':
    main()
