from storage.HeapFile import HeapFile
from storage.Record import Record
import os
import json

def crear_tabla():
    base_dir   = os.path.dirname(os.path.abspath(__file__))
    tables_dir = os.path.join(base_dir, "tables")

    table_name = input("Introduce el nombre de la tabla (sin extensión .dat): ")
    filename   = os.path.join(tables_dir, f"{table_name}.dat")

    if os.path.exists(filename):
        print(f"La tabla {table_name} ya existe.")
        return

    schema = []
    while True:
        field_name = input("Introduce el nombre del campo: ")
        field_type = input("Introduce el tipo de campo (i = int, f = float, s = string): ")
        if field_type == 's':
            size = int(input("Introduce el tamaño del campo (para strings): "))
            schema.append((field_name, f"{size}s"))
        else:
            schema.append((field_name, field_type))

        if input("¿Deseas agregar otro campo? (si/no): ").strip().lower() != 'si':
            break

    print("Creando nueva tabla...")
    HeapFile.build_file(filename, schema)
    print(f"Tabla {table_name} creada exitosamente.")

def interactuar_con_tabla():
    base_dir   = os.path.dirname(os.path.abspath(__file__))
    tables_dir = os.path.join(base_dir, "tables")

    table_name = input("Introduce el nombre de la tabla (sin extensión .dat): ")
    filename   = os.path.join(tables_dir, f"{table_name}.dat")

    if not os.path.exists(filename):
        print(f"La tabla {table_name} no existe.")
        return

    heap = HeapFile(filename)

    while True:
        print("\nOpciones disponibles:")
        print("1. Insertar un nuevo registro")
        print("2. Cargar todo el contenido de la tabla")
        print("3. Buscar por id")
        print("4. Volver al menú principal")
        opc = input("Elige una opción: ").strip()

        if opc == '1':
            valores = []
            for name, ftype in heap.schema:
                if ftype == 'i':
                    v = int(input(f"{name} (entero): "))
                elif ftype == 'f':
                    v = float(input(f"{name} (flotante): "))
                else:  # string fijo
                    raw = input(f"{name} (cadena): ")
                    size = int(ftype[:-1])
                    v = raw[:size].ljust(size)
                valores.append(v)

            rec = Record(heap.schema, valores)
            heap.insert_record(rec)
            print("Registro insertado.")

        elif opc == '2':
            print("\nContenido actual:")
            heap.load()

        elif opc == '3':
            target_id = input("Introduce el ID del registro a buscar: ")
            heap.search_record(target_id)

        elif opc == '4':
            break
        else:
            print("Opción no válida.")

def main():
    while True:
        print("\nMenú principal:")
        print("1. Crear nueva tabla")
        print("2. Interactuar con tabla existente")
        print("3. Salir")
        ch = input("Elige una opción: ").strip()

        if ch == '1':
            crear_tabla()
        elif ch == '2':
            interactuar_con_tabla()
        elif ch == '3':
            print("Saliendo.")
            break
        else:
            print("Opción no válida.")

if __name__ == "__main__":
    main()
