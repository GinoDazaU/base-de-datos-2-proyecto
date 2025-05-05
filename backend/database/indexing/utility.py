import json

def load_schema(schema_path):
    """Carga el esquema JSON y devuelve una lista de campos con nombre y tipo."""
    with open(schema_path, "r") as f:
        data = json.load(f)
        return data["fields"]

def get_field_index(fields, name):
    """Devuelve el índice del campo con nombre 'name' en la lista de campos."""
    for i, field in enumerate(fields):
        if field["name"] == name:
            return i
    raise ValueError(f"El campo '{name}' no se encuentra en el esquema.")

def get_field_type(fields, name):
    """Devuelve el tipo de datos del campo 'name' (por ejemplo, 'i', 'f', '20s')."""
    for field in fields:
        if field["name"] == name:
            return field["type"]
    raise ValueError(f"El campo '{name}' no se encuentra en el esquema.")