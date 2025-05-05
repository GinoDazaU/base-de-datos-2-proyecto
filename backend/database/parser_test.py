import re
import os
from storage.HeapFile import HeapFile
from storage.Record import Record

BASE_DIR   = os.path.dirname(os.path.abspath(__file__))
TABLES_DIR = os.path.join(BASE_DIR, "tables")

def parse_create_table(sql: str):
    m = re.match(r"CREATE TABLE (\w+)\s*\((.+)\);?", sql, re.IGNORECASE)
    if not m:
        print("Sintaxis inválida para CREATE TABLE.")
        return
    name, fields_raw = m.group(1), m.group(2)
    schema = []
    for part in fields_raw.split(","):
        fn, ft = part.strip().split()
        schema.append((fn, ft))
    dat = os.path.join(TABLES_DIR, f"{name}.dat")
    if os.path.exists(dat):
        print(f"La tabla {name} ya existe.")
        return
    HeapFile.build_file(dat, schema)
    print(f"Tabla {name} creada.")

def parse_insert_values(sql: str):
    m = re.match(r"INSERT INTO (\w+)\s+VALUES\s*\((.+)\);?", sql, re.IGNORECASE)
    if not m:
        print("Sintaxis inválida para INSERT INTO ... VALUES ...")
        return
    name, vals_raw = m.group(1), m.group(2)
    dat = os.path.join(TABLES_DIR, f"{name}.dat")
    if not os.path.exists(dat):
        print(f"La tabla {name} no existe.")
        return
    heap = HeapFile(dat)
    parts = [v.strip() for v in re.split(r",(?=(?:[^']*'[^']*')*[^']*$)", vals_raw)]
    values = []
    for (fn, ft), raw in zip(heap.schema, parts):
        if ft == 'i':
            values.append(int(raw))
        elif ft == 'f':
            values.append(float(raw))
        elif ft.endswith('s'):
            # strip single or double quotes if present
            s = raw.strip()
            if (s.startswith("'") and s.endswith("'")) or (s.startswith('"') and s.endswith('"')):
                s = s[1:-1]
            size = int(ft[:-1])
            values.append(s[:size].ljust(size))
        else:
            values.append(raw)
    rec = Record(heap.schema, values)
    heap.insert_record(rec)
    print(f"Registro insertado en {name}: {values}")

def parse_insert_select(sql: str):
    m = re.match(r"INSERT INTO (\w+)\s+SELECT \* FROM (\w+);?", sql, re.IGNORECASE)
    if not m:
        print("Sintaxis inválida para INSERT ... SELECT ...")
        return
    tgt, src = m.group(1), m.group(2)
    src_dat = os.path.join(TABLES_DIR, f"{src}.dat")
    tgt_dat = os.path.join(TABLES_DIR, f"{tgt}.dat")
    if not os.path.exists(src_dat):
        print(f"Tabla origen {src} no existe.")
        return
    if not os.path.exists(tgt_dat):
        print(f"Tabla destino {tgt} no existe.")
        return
    src_h = HeapFile(src_dat)
    tgt_h = HeapFile(tgt_dat)
    with open(src_dat, "rb") as f:
        f.seek(HeapFile.METADATA_SIZE)
        while True:
            buf = f.read(src_h.record_size)
            if not buf or len(buf) < src_h.record_size:
                break
            rec = Record.unpack(buf, src_h.schema)
            tgt_h.insert_record(rec)
    print(f"Copiados registros de {src} a {tgt}.")

def parse_select(sql: str):
    m = re.match(r"SELECT \* FROM (\w+);?", sql, re.IGNORECASE)
    if not m:
        print("Sintaxis inválida para SELECT * FROM ...")
        return
    name = m.group(1)
    dat = os.path.join(TABLES_DIR, f"{name}.dat")
    if not os.path.exists(dat):
        print(f"Tabla {name} no existe.")
        return
    h = HeapFile(dat)
    print(f"Contenido de {name}:")
    h.print_all()

def run_sql(sql: str):
    s = sql.strip()
    if s.lower().startswith("create table"):
        parse_create_table(s)
    elif s.lower().startswith("insert into") and "values" in s.lower():
        parse_insert_values(s)
    elif s.lower().startswith("insert into") and "select" in s.lower():
        parse_insert_select(s)
    elif s.lower().startswith("select *"):
        parse_select(s)
    else:
        print(f"Comando no reconocido: {s}")

if __name__ == "__main__":
    # Tabla productos
    run_sql("CREATE TABLE productos (id i, nombre 20s, precio f, cantidad i);")
    run_sql("INSERT INTO productos VALUES (1, 'Galletas', 3.5, 10);")
    run_sql("INSERT INTO productos VALUES (2, 'Chocolate', 5.2, 8);")
    run_sql("INSERT INTO productos VALUES (3, 'Jugo de Naranja', 4.0, 20);")
    run_sql("INSERT INTO productos VALUES (4, 'Pan Integral', 2.3, 15);")
    run_sql("INSERT INTO productos VALUES (5, 'Queso', 7.8, 5);")
    run_sql("SELECT * FROM productos;")

    run_sql("CREATE TABLE backup (id i, nombre 20s, precio f, cantidad i);")
    run_sql("INSERT INTO backup SELECT * FROM productos;")
    run_sql("SELECT * FROM backup;")


    # Tabla clientes
    run_sql("CREATE TABLE clientes (id i, nombre 30s, email 40s, edad i, telefono 15s, ciudad 20s, saldo f, vip i);")
    run_sql("INSERT INTO clientes VALUES (1, 'Ana Torres', 'ana.torres@gmail.com', 29, '987654321', 'Lima', 1200.50, 1);")
    run_sql("INSERT INTO clientes VALUES (2, 'Luis Pérez', 'luisp@hotmail.com', 35, '912345678', 'Cusco', 850.75, 0);")
    run_sql("INSERT INTO clientes VALUES (3, 'María López', 'mlopez@yahoo.com', 42, '900111222', 'Arequipa', 432.00, 1);")
    run_sql("INSERT INTO clientes VALUES (4, 'Carlos Díaz', 'carlos.diaz@outlook.com', 27, '987112233', 'Lima', 1570.00, 0);")
    run_sql("INSERT INTO clientes VALUES (5, 'Sofía Ramírez', 'sofiaramirez@gmail.com', 31, '921223344', 'Piura', 300.25, 1);")
    run_sql("INSERT INTO clientes VALUES (6, 'Daniel Vega', 'daniel.vega@gmail.com', 45, '988887777', 'Trujillo', 675.00, 0);")
    run_sql("SELECT * FROM clientes;")
    
    run_sql("CREATE TABLE clientes_backup (id i, nombre 30s, email 40s, edad i, telefono 15s, ciudad 20s, saldo f, vip i);")
    run_sql("INSERT INTO clientes_backup SELECT * FROM clientes;")
    run_sql("SELECT * FROM clientes_backup;")
