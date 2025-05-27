import os
import sys

# Ajustar el path para poder importar desde el backend
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from database.indexing.BPlusTreeIndex import BPlusTreeIndex
from database.indexing.IndexRecord import IndexRecord


import os

def test_btree_minimo():
    # Preparación
    order = 3
    index_format = "10s"  # Strings de hasta 10 caracteres
    table_name = "btree_simple_test"
    auxfile = table_name + ".btree.idx"

    # Elimina archivo viejo si existe
    if os.path.exists(auxfile):
        os.remove(auxfile)

    # Crear índice vacío
    btree = BPlusTreeIndex(order, filename="dummy.dat", auxname=auxfile, index_format=index_format)

    # Insertar claves manualmente
    claves = ["ANA", "CARLOS", "LUCIA", "BEA", "PEDRO"]
    offsets = [10, 20, 30, 40, 50]

    for clave, offset in zip(claves, offsets):
        rec = IndexRecord(index_format, clave, offset)
        btree.insert(rec)

    # Buscar claves insertadas
    for clave in claves:
        resultados = btree.search(clave)
        print(f"[BÚSQUEDA] Clave: {clave} → Offsets encontrados: {resultados}")

    # Buscar clave que no existe
    no_existente = "MARIO"
    resultado = btree.search(no_existente)
    print(f"[BÚSQUEDA] Clave inexistente '{no_existente}' → {resultado}")

    btree.scan_all()

if __name__ == "__main__":
    test_btree_minimo()
    