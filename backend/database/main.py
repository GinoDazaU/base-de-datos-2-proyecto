import os
from storage.HeapFile import HeapFile
from storage.Record import Record
from indexing.SequentialIndex import SequentialIndex

# Configuración inicial - crear carpeta tables si no existe
base_dir = os.path.dirname(os.path.abspath(__file__))
tables_dir = os.path.join(base_dir, "tables")
os.makedirs(tables_dir, exist_ok=True)

def get_table_path(table_name):
    """Obtiene la ruta completa del archivo de tabla"""
    return os.path.join(tables_dir, table_name)

def get_index_path(table_name, field_name):
    """Obtiene la ruta completa del archivo de índice"""
    table_path = get_table_path(table_name)
    base, _ = os.path.splitext(table_path)
    return f"{base}"

def crear_tabla():
    table_name = input("Introduce el nombre de la tabla (sin extensión .dat): ")
    filename = get_table_path(table_name)

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
    table_name = input("Introduce el nombre de la tabla (sin extensión .dat): ")
    filename = get_table_path(table_name)

    if not os.path.exists(filename + ".dat"):
        print(f"La tabla {table_name} no existe.")
        return

    heap = HeapFile(filename)

    while True:
        print("\nOpciones disponibles:")
        print("1. Insertar un nuevo registro")
        print("2. Cargar todo el contenido de la tabla")
        print("3. Buscar por id")
        print("4. Crear un índice secuencial")
        print("5. Buscar usando un índice")
        print("6. Buscar rango usando un índice")
        print("7. Mostrar contenido de un índice")
        print("8. Volver al menú principal")
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
            heap.print_all()

        elif opc == '3':
            target_id = input("Introduce el ID del registro a buscar: ")
            heap.search_record(target_id)

        elif opc == '4':
            field_name = input("Introduce el campo a indexar: ")
            if field_name not in [field[0] for field in heap.schema]:
                print(f"El campo {field_name} no existe en la tabla.")
                continue
            # Se llama a build_index sin la extensión .dat
            SequentialIndex.build_index(filename, heap.extract_index, field_name)
            print(f"Índice para {field_name} creado.")

        elif opc == '5':
            field_name = input("Introduce el campo indexado: ")
            index_path = get_index_path(table_name, field_name)
            if not os.path.exists(index_path):
                print(f"No existe índice para {field_name}")
                continue
            
            key = input(f"Introduce el valor de {field_name} a buscar: ")
            field_type = next(ftype for name, ftype in heap.schema if name == field_name)
            try:
                key = int(key) if field_type == 'i' else float(key) if field_type == 'f' else key
            except ValueError:
                print("Tipo de dato incorrecto")
                continue
            
            index = SequentialIndex(index_path)
            index_rec = index.search_record(key)
            if index_rec:
                record = heap.fetch_record_by_offset(index_rec.offset)
                print("Registro encontrado:")
                record.print()
            else:
                print("Registro no encontrado")

        elif opc == '6':
            field_name = input("Introduce el campo indexado: ")
            index_path = get_index_path(table_name, field_name)
            if not os.path.exists(index_path):
                print(f"No existe índice para {field_name}")
                continue
            
            field_type = next(ftype for name, ftype in heap.schema if name == field_name)
            try:
                start = input("Valor inicial del rango: ")
                end = input("Valor final del rango: ")
                start = int(start) if field_type == 'i' else float(start) if field_type == 'f' else start
                end = int(end) if field_type == 'i' else float(end) if field_type == 'f' else end
            except ValueError:
                print("Tipo de dato incorrecto")
                continue
            
            index = SequentialIndex(index_path)
            index_recs = index.search_range(start, end)
            print(f"\n{len(index_recs)} registros encontrados:")
            for idx_rec in index_recs:
                record = heap.fetch_record_by_offset(idx_rec.offset)
                record.print()

        elif opc == '7':
            field_name = input("Introduce el campo indexado: ")
            index_path = get_index_path(table_name, field_name)
            if not os.path.exists(index_path + "." + field_name + ".seq.idx"):
                print(f"No existe índice para {field_name}")
                continue
            index = SequentialIndex(index_path, field_name)
            index.print_all()

        elif opc == '8':
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
