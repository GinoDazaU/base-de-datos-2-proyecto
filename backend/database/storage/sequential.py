import struct
import csv
import math
import os

class Record:

    FORMAT = "i30sif10s"
    SIZE = struct.calcsize(FORMAT)

    def __init__(self, id: int, nombre: str, cantidad_vendida: int, precio_unitario: float, fecha: str):
        self.id = id
        self.nombre = nombre
        self.cantidad_vendida = cantidad_vendida
        self.precio_unitario = precio_unitario
        self.fecha = fecha

    def pack(self):
        nombre = self.nombre[:30].ljust(30, '\x00')
        fecha = self.fecha[:10].ljust(10, '\x00')
        
        return struct.pack(
            self.FORMAT,
            self.id,
            nombre.encode('utf-8'),
            self.cantidad_vendida,
            self.precio_unitario,
            fecha.encode('utf-8')
        )
    
    @staticmethod
    def unpack(record_buffer):
        id, nombre, cantidad_vendida, precio_unitario, fecha = struct.unpack(Record.FORMAT, record_buffer)
        return Record(
            id,
            nombre.decode('utf-8').rstrip('\x00'),
            cantidad_vendida,
            precio_unitario,
            fecha.decode('utf-8').rstrip('\x00')
        )
    
    def print(self):
        print(f"Id: {self.id} | Nombre: {self.nombre} | Cantidad Vendida: {self.cantidad_vendida} | Precio unitario: {self.precio_unitario} | Fecha: {self.fecha}")
    
class SecuentialRecorder:

    METADATA_FORMAT = ("iii")
    METADATA_SIZE = struct.calcsize(METADATA_FORMAT)

    def __init__(self, filename):
        self.filename = filename

        if os.path.exists(filename):
            with open(filename, "rb") as file:
                metadata_buffer = file.read(self.METADATA_SIZE)
                self.main_size, self.aux_size, self.max_aux_size = struct.unpack(self.METADATA_FORMAT, metadata_buffer)
        else:
            with open(filename, "wb") as file:
                self.main_size = 0
                self.aux_size = 0
                self.max_aux_size = 1
                metadata_buffer = struct.pack(self.METADATA_FORMAT, self.main_size, self.aux_size, self.max_aux_size)
                file.write(metadata_buffer)


    def update_metadata(self):
        with open(self.filename, "r+b") as file:
            metadata_buffer = struct.pack(self.METADATA_FORMAT, self.main_size, self.aux_size, self.max_aux_size)
            file.write(metadata_buffer)

    def insert_record(self, record: Record):
        """Inserta un registro en el area auxiliar y reconstruye si es necesario"""

        # 0. Verificar que el registro no exista
        if self.search_record(record.id) != None:
            print(f"El registro con id: {record.id} ya existe")
            return False

        # 1. Escribir en área auxiliar
        with open(self.filename, "r+b") as file:
            # Posicionarse al final del área auxiliar
            file.seek(self.METADATA_SIZE + self.main_size * Record.SIZE + self.aux_size * Record.SIZE)
            file.write(record.pack())
            self.aux_size += 1
            self.update_metadata()
            print("Registro insertado correctamente")
        
        # 2. Reconstruir si se excede el límite
        if self.aux_size > self.max_aux_size:
            print("Zona auxiliar llena, reconstruyendo archivo...")
            self.rebuild_file()

    def rebuild_file(self):
        """Reconstruye el archivo fusionando areas principal y auxiliar"""
        # 1. Leer todos los registros activos
        active_records = []
        
        # Leer área principal
        with open(self.filename, "rb") as file:
            file.seek(self.METADATA_SIZE)
            for _ in range(self.main_size):
                buffer = file.read(Record.SIZE)
                if not buffer: break
                record = Record.unpack(buffer)
                if record.id != -1:
                    active_records.append(record)
        
        # Leer área auxiliar
        with open(self.filename, "rb") as file:
            file.seek(self.METADATA_SIZE + self.main_size * Record.SIZE)
            for _ in range(self.aux_size):
                buffer = file.read(Record.SIZE)
                if not buffer: break
                record = Record.unpack(buffer)
                if record.id != -1:
                    active_records.append(record)
        
        # 2. Ordenar por ID (insertion sort)
        for i in range(1, len(active_records)):
            key = active_records[i]
            j = i - 1
            while j >= 0 and active_records[j].id > key.id:
                active_records[j + 1] = active_records[j]
                j -= 1
            active_records[j + 1] = key
        
        # 3. Calcular nuevo tamaño auxiliar
        new_main_size = len(active_records)
        new_max_aux = max(1, math.floor(math.log2(new_main_size))) if new_main_size > 0 else 1

        
        # 4. Escribir el nuevo archivo
        temp_filename = self.filename + ".tmp"
        with open(temp_filename, "wb") as file:
            # Escribir metadata
            metadata = struct.pack(self.METADATA_FORMAT, new_main_size, 0, new_max_aux)
            file.write(metadata)
            
            # Escribir registros principales
            for record in active_records:
                file.write(record.pack())
            
            # Escribir area auxiliar vacia
            empty_record = Record(-1, "", 0, 0.0, "").pack()
            for _ in range(new_max_aux):
                file.write(empty_record)
        
        # 5. Reemplazar archivo
        os.replace(temp_filename, self.filename)
        
        # 6. Actualizar metadatos
        self.main_size = new_main_size
        self.aux_size = 0
        self.max_aux_size = new_max_aux

    def search_record(self, id: int):
        """Busca un registro por ID usando búsqueda binaria (principal) + secuencial (auxiliar)"""
        # 1. Busqueda binaria en area principal
        with open(self.filename, "rb") as file:
            file.seek(self.METADATA_SIZE)
            left, right = 0, self.main_size - 1
            
            while left <= right:
                mid = (left + right) // 2
                file.seek(self.METADATA_SIZE + mid * Record.SIZE)
                buffer = file.read(Record.SIZE)
                record = Record.unpack(buffer)
                
                if record.id == id:
                    return record
                elif record.id < id:
                    left = mid + 1
                else:
                    right = mid - 1
        
        # 2. Busqueda secuencial en area auxiliar (cargada en RAM)
        with open(self.filename, "rb") as file:
            file.seek(self.METADATA_SIZE + self.main_size * Record.SIZE)
            for _ in range(self.aux_size):
                buffer = file.read(Record.SIZE)
                record = Record.unpack(buffer)
                if record.id == id:
                    return record
        
        return None
    
    def delete_record(self, id: int):
        """Lo mismo que el search_record, esta vez al encontrar el registro lo reemplaza por uno vacio"""
        """Elimina lógicamente un registro marcando su ID como -1"""
        # 1. Buscar el registro en el area principal
        with open(self.filename, "r+b") as file:
            file.seek(self.METADATA_SIZE)
            left, right = 0, self.main_size - 1
            
            while left <= right:
                mid = (left + right) // 2
                file.seek(self.METADATA_SIZE + mid * Record.SIZE)
                buffer = file.read(Record.SIZE)
                record = Record.unpack(buffer)
                
                if record.id == id:
                    # Encontrado en area principal - retroceder y escribir -1
                    file.seek(-Record.SIZE, os.SEEK_CUR)
                    empty_record = Record(-1, "", 0, 0.0, "").pack()
                    file.write(empty_record)
                    return True
                elif record.id < id:
                    left = mid + 1
                else:
                    right = mid - 1
        
        # 2. Buscar en el area auxiliar
        with open(self.filename, "r+b") as file:
            file.seek(self.METADATA_SIZE + self.main_size * Record.SIZE)
            for _ in range(self.aux_size):
                pos = file.tell()
                buffer = file.read(Record.SIZE)
                record = Record.unpack(buffer)
                
                if record.id == id:
                    # Encontrado en area auxiliar - retroceder y escribir -1
                    file.seek(pos)
                    empty_record = Record(-1, "", 0, 0.0, "").pack()
                    file.write(empty_record)
                    return True
        
        return False
    
    def search_range(self, start_id: int, end_id: int) -> list[Record]:
        """Busca registros en el rango [start_id, end_id]"""
        results = []
        
        # 1. Búsqueda en área principal (ordenada)
        with open(self.filename, "rb") as file:
            file.seek(self.METADATA_SIZE)
            
            # Encontrar el primer ID >= start_id con búsqueda binaria
            left, right = 0, self.main_size - 1
            start_pos = 0
            
            while left <= right:
                mid = (left + right) // 2
                file.seek(self.METADATA_SIZE + mid * Record.SIZE)
                buffer = file.read(Record.SIZE)
                record = Record.unpack(buffer)
                
                if record.id < start_id:
                    left = mid + 1
                else:
                    right = mid - 1
                    start_pos = mid
            
            # Recorrer secuencialmente desde start_pos
            file.seek(self.METADATA_SIZE + start_pos * Record.SIZE)
            for _ in range(start_pos, self.main_size):
                buffer = file.read(Record.SIZE)
                if not buffer: break
                
                record = Record.unpack(buffer)
                if record.id > end_id:
                    break
                if start_id <= record.id <= end_id and record.id != -1:
                    results.append(record)
        
        # 2. Búsqueda en área auxiliar (secuencial)
        with open(self.filename, "rb") as file:
            file.seek(self.METADATA_SIZE + self.main_size * Record.SIZE)
            for _ in range(self.aux_size):
                buffer = file.read(Record.SIZE)
                if not buffer: break
                
                record = Record.unpack(buffer)
                if start_id <= record.id <= end_id and record.id != -1:
                    results.append(record)
        
        return results

    def load(self):
        with open(self.filename, 'rb') as file:
            metadata_buffer = file.read(self.METADATA_SIZE)
            main_size, aux_size, max_aux_size = struct.unpack(self.METADATA_FORMAT, metadata_buffer)
            records = []
            for i in range(main_size + aux_size):
                record_buffer = file.read(Record.SIZE)
                records.append(Record.unpack(record_buffer))

            print("\nMetadata:")
            print(f"Tamaño de la zona principal: {main_size}")
            print(f"Tamaño de la zona auxiliar: {aux_size}")
            print(f"Tamaño maximo de la zona auxiliar: {max_aux_size}")
            print("Registros en zona principal:")
            for i in range(main_size + aux_size):
                if i == main_size:
                    print("\nRegistros en zona auxiliar: ")
                records[i].print()

    def load_from_csv(self, csv_filename):
        """Loads and inserts all records from a CSV file"""
        with open(csv_filename, 'r', encoding='utf-8') as csvfile:
            reader = csv.reader(csvfile)
            for row in reader:
                try:
                    # Parse CSV row (assuming format: id,nombre,cantidad,precio,fecha)
                    record_id = int(row[0])
                    nombre = row[1]
                    cantidad = int(row[2])
                    precio = float(row[3])
                    fecha = row[4]
                    
                    # Create and insert record
                    record = Record(record_id, nombre, cantidad, precio, fecha)
                    self.insert_record(record)
                    
                except (ValueError, IndexError) as e:
                    print(f"Error processing row {row}: {e}")
                    continue


#---------------------------
#         TESTING
#---------------------------

def main():
    # Inicializacion
    print("\n--- INICIALIZAR ARCHIVO NUEVO ---")
    registrador = SecuentialRecorder("test.dat")

    # Caso 1: Inserciones basicas
    print("\n--- CASO 1: Inserciones basicas ---")
    registrador.insert_record(Record(3, "Producto C", 15, 3.5, "2023-01-03"))
    registrador.insert_record(Record(1, "Producto A", 10, 1.0, "2023-01-01"))
    registrador.insert_record(Record(2, "Producto B", 20, 2.0, "2023-01-02"))
    registrador.load()

    # Caso 2: Intento de ID duplicado
    print("\n--- CASO 2: Intento de ID duplicado ---")
    registrador.insert_record(Record(2, "Producto B Duplicado", 99, 9.99, "2023-09-09"))
    registrador.load()

    # Caso 3: Eliminacion de registro
    print("\n--- CASO 3: Eliminacion de registro ---")
    print("Antes de eliminar:")
    registrador.load()
    registrador.delete_record(2)
    print("\nDespues de eliminar ID 2:")
    registrador.load()

    # Caso 4: Eliminar registro inexistente
    print("\n--- CASO 4: Eliminar registro inexistente ---")
    resultado = registrador.delete_record(99)
    print(f"Resultado eliminar ID 99: {'Exito' if resultado else 'Fallo'}")
    registrador.load()

    # Caso 5: Reconstruccion automatica
    print("\n--- CASO 5: Reconstruccion automatica ---")
    print("Estado inicial:")
    registrador.load()
    print("\nLlenando area auxiliar...")
    registrador.insert_record(Record(4, "Producto D", 40, 4.0, "2023-01-04"))
    registrador.insert_record(Record(5, "Producto E", 50, 5.0, "2023-01-05"))
    print("\nDespues de inserciones:")
    registrador.load()

    # Caso 6: Busquedas de registros
    print("\n--- CASO 6: Busquedas de registros ---")
    print("Buscar ID existente (3):")
    print(registrador.search_record(3).print() if registrador.search_record(3) else print("No encontrado"))
    print("\nBuscar ID eliminado (2):")
    print(registrador.search_record(2).print() if registrador.search_record(2) else print("No encontrado"))
    print("\nBuscar ID inexistente (100):")
    print(registrador.search_record(100).print() if registrador.search_record(100) else print("No encontrado"))

    # Caso 7: Eliminaciones multiples y reconstruccion
    print("\n--- CASO 7: Eliminaciones multiples y reconstruccion ---")
    registrador.delete_record(1)
    registrador.delete_record(3)
    print("Despues de eliminar IDs 1 y 3:")
    registrador.load()
    print("\nInsertando registro para forzar reconstruccion:")
    registrador.insert_record(Record(6, "Producto F", 60, 6.0, "2023-01-06"))
    registrador.load()

    #---------------------------
    #    PRUEBAS BUSQUEDA POR RANGO
    #---------------------------

    print("\n--- PRUEBAS BUSQUEDA POR RANGO ---")

    # Preparar datos de prueba
    registrador.insert_record(Record(10, "Producto J", 100, 10.0, "2023-01-10"))
    registrador.insert_record(Record(15, "Producto O", 150, 15.0, "2023-01-15"))
    registrador.insert_record(Record(20, "Producto T", 200, 20.0, "2023-01-20"))

    # Rango 1: Dentro de area principal
    print("\n--- Rango 5-15 (area principal) ---")
    for r in registrador.search_range(5, 15):
        r.print()

    # Rango 2: Cruza areas principal+auxiliar
    print("\n--- Rango 18-25 (principal+auxiliar) ---")
    for r in registrador.search_range(18, 25):
        r.print()

    # Rango 3: Sin resultados
    print("\n--- Rango 100-200 (sin resultados) ---")
    print(len(registrador.search_range(100, 200)), "registros encontrados")

    # Rango 4: Incluyendo eliminados
    registrador.insert_record(Record(12, "Producto L", 120, 12.0, "2023-01-12"))
    registrador.delete_record(12)
    print("\n--- Rango 10-20 (incluyendo eliminados) ---")
    for r in registrador.search_range(10, 20):
        r.print()  # No debe mostrar ID 12

    # Rango 5: Coincidencia exacta
    print("\n--- Rango 15-15 (coincidencia exacta) ---")
    for r in registrador.search_range(15, 15):
        r.print()



    # Si desea puede cargar los registros desde del dataset
    # esto estara mas detallado en p1_testing.py

    # registrador2 = SecuentialRecorder("test.dat")
    # registrador2.load_from_csv("sales_dataset.csv")