from database import *

def crear_tabla():
    table_name = input("Introduce el nombre de la tabla (sin extensión .dat): ")
    filename = get_table_path(table_name)

    if os.path.exists(filename + ".dat"):
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
    create_table(table_name, schema)
    print(f"Tabla {table_name} creada exitosamente.")

def interactuar_con_tabla():
    table_name = input("Introduce el nombre de la tabla (sin extensión .dat): ")
    table_path = get_table_path(table_name)

    if not os.path.exists(table_path + ".dat"):
        print(f"La tabla {table_name} no existe.")
        return

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
            # Necesitamos cargar el schema primero
            heap = HeapFile(table_path)
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
            insert_record(table_name, rec)
            print("Registro insertado.")

        elif opc == '2':
            print_table(table_name)

        elif opc == '3':
            heap = HeapFile(table_path)
            target_id = input("Introduce el ID del registro a buscar: ")
            heap.search_record(target_id)

        elif opc == '4':
            heap = HeapFile(table_path)
            field_name = input("Introduce el campo a indexar: ")
            if field_name not in [field[0] for field in heap.schema]:
                print(f"El campo {field_name} no existe en la tabla.")
                continue
            create_seq_idx(table_name, field_name)
            print(f"Índice secuencial para {field_name} creado.")

        elif opc == '5':
            field_name = input("Introduce el campo indexado: ")
            search_seq_idx(table_name, field_name, input(f"Introduce el valor de {field_name} a buscar: "))

        elif opc == '6':
            field_name = input("Introduce el campo indexado: ")
            heap = HeapFile(table_path)
            field_type = next(ftype for name, ftype in heap.schema if name == field_name)
            try:
                start = input("Valor inicial del rango: ")
                end = input("Valor final del rango: ")
                start = int(start) if field_type == 'i' else float(start) if field_type == 'f' else start
                end = int(end) if field_type == 'i' else float(end) if field_type == 'f' else end
                search_seq_idx(table_name, field_name, (start, end))
            except ValueError:
                print("Tipo de dato incorrecto")

        elif opc == '7':
            field_name = input("Introduce el campo indexado: ")
            print_all_seq_idx(table_name, field_name)

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