import os
import sys
import json

# Agregar ruta padre al path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

def generate_database_structure():
    parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    tables_path = os.path.join(parent_dir, "database", "tables")
    output = {
        "db": "MY DB",
        "tables": []
    }

    for filename in os.listdir(tables_path):
        if filename.startswith("inverted_index") or not filename.endswith(".json"):
            continue

        file_path = os.path.join(tables_path, filename)
        
        with open(file_path, 'r', encoding='utf-8') as file:
            table_data = json.load(file)

            # Parse fields
            fields = []
            for field in table_data.get("fields", []):
                fields.append({
                    "name": field["name"],
                    "type": field["type"],
                    "is_primary_key": field.get("is_primary_key", False)
                })

            # Create btree indexes for primary keys
            indexes = []
            for field in fields:
                if field["is_primary_key"]:
                    indexes.append({
                        "field_name": field["name"],
                        "type": "btree"
                    })

            output["tables"].append({
                "table_name": table_data["table_name"],
                "fields": fields,
                "indexes": indexes
            })

    return output


if __name__ == "__main__":
    result = generate_database_structure()
    print(json.dumps(result, indent=4))
