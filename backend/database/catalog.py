import os
import json

def map_type(short_type):
    type_map = {
        "i": "integer",
        "f": "float",
        "s": "character varying",
        "20s": "character varying(20)",
        "15s": "character varying(15)"
    }
    return type_map.get(short_type, "text")

def parse_schema_file(path):
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    table_name = data.get("table_name")
    fields = []
    for field in data.get("fields", []):
        fields.append({
            "name": field["name"],
            "isPK": field.get("is_primary_key", False),
            "dataType": map_type(field["type"])
        })
    return table_name, fields

def parse_index_filename(filename):
    parts = filename.split('.')
    if len(parts) < 3:
        return None
    return parts[0], parts[1], parts[2]

def build_json_structure(base_folder, db_name):
    tables = {}

    # Leer todos los schemas para tablas y columnas
    for file in os.listdir(base_folder):
        if file.endswith('.schema.json'):
            full_path = os.path.join(base_folder, file)
            table_name, fields = parse_schema_file(full_path)
            tables[table_name] = {
                "id": f"tbl_{table_name}",
                "name": table_name,
                "type": "table",
                "children": [
                    {
                        "id": f"fld_cols_{table_name}",
                        "name": "Columns",
                        "type": "folder",
                        "children": [
                            {
                                "id": f"col_{table_name}_{field['name']}",
                                "isPK": field["isPK"],
                                "name": field["name"],
                                "type": "column",
                                "dataType": field["dataType"]
                            }
                            for field in fields
                        ]
                    },
                    {
                        "id": f"fld_idx_{table_name}",
                        "name": "Indexes",
                        "type": "folder",
                        "children": []
                    }
                ]
            }

    # Leer archivos índices tipo tabla.campo.tipoIndice
    for file in os.listdir(base_folder):
        if not file.endswith('.schema.json'):
            parsed = parse_index_filename(file)
            if parsed:
                tabla, campo, tipo_indice = parsed
                if tabla in tables:
                    idx_id = f"idx_{tabla}_{campo}"
                    idx_name = f"{tabla}_{campo}"
                    # tipo de índice en minúscula excepto si es PRIMARY KEY
                    idx_type = tipo_indice.upper() if tipo_indice.lower() == "pkey" else tipo_indice.lower()

                    tables[tabla]["children"][1]["children"].append({
                        "id": idx_id,
                        "name": idx_name,
                        "type": "index",
                        "indexType": idx_type
                    })

    return [
        {
            "id": f"db_{db_name}",
            "name": db_name,
            "type": "database",
            "children": list(tables.values())
        }
    ]

if __name__ == "__main__":
    base_path = "backend/database/tables"  # Carpeta donde están los archivos
    db_name = "MY_DB"

    structure = build_json_structure(base_path, db_name)
    print(json.dumps(structure, indent=4, ensure_ascii=False))
