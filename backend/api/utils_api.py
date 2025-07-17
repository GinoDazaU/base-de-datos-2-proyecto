import os
import sys
import json
import re
import pandas as pd
from collections import defaultdict

from mutagen import File as MutagenFile
# Agregar ruta padre al path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from backend.database.global_utils import Utils
from backend.database.fancytypes.column_types import QueryResult
from backend.api.mock import *
from backend.database.yarasca import Parser, query_run

from backend.database.scanner import Scanner
from backend.database.visitor import RunVisitor
import time


def normalize_type(t):
    t = t.strip().lower()
    if re.match(r"^\d+s$", t):
        return f"VARCHAR({t[:-1]})"
    if re.match(r"^i+$", t):
        return f"TUPLE(INT,{len(t)})" if len(t) > 1 else "INT"
    if re.match(r"^f+$", t):
        return f"TUPLE(FLOAT,{len(t)})" if len(t) > 1 else "FLOAT"
    if t == "text":
        return "TEXT"
    return t.upper()


def generate_database_structure():
    tables_path = Utils.build_path("tables")
    output = {
        "db": "MY DB",
        "tables": []
    }

    tables_dict = {}
    inverted_indexes = defaultdict(list)  # {table_name: [field_name, ...]}

    for filename in os.listdir(tables_path):
        if not filename.endswith(".json"):
            continue

        parts = filename.split('.')
        if len(parts) == 3:
            table_name, mid, ext = parts
            if mid != "schema" or ext != "json":
                continue
            if table_name in ["inverted_index", "inverted_index_norms"]:
                continue

            # Leer archivo de tabla
            file_path = os.path.join(tables_path, filename)
            with open(file_path, 'r', encoding='utf-8') as file:
                table_data = json.load(file)

            # Procesar campos y tipos
            fields = []
            for field in table_data.get("fields", []):
                fields.append({
                    "name": field["name"],
                    "type": normalize_type(field["type"]),
                    "is_primary_key": field.get("is_primary_key", False)
                })

            # Crear índices BTREE para claves primarias
            indexes = []
            for field in fields:
                if field["is_primary_key"]:
                    indexes.append({
                        "field_name": field["name"],
                        "type": "BTREE"
                    })

            tables_dict[table_data["table_name"]] = {
                "table_name": table_data["table_name"],
                "fields": fields,
                "indexes": indexes
            }

        elif len(parts) == 4:
            table_name, field_name, mid, ext = parts
            if mid != "schema" or ext != "json":
                continue
            inverted_indexes[table_name].append(field_name)
            # Caso especial: 5 partes (ej: songs.sound_file.idx.schema.json)
        elif len(parts) == 5:
            table_name, field_name, idx, mid, ext = parts
            if idx != "idx" or mid != "schema" or ext != "json":
                continue
            if table_name not in tables_dict:
                continue

            # Revisar si el campo existe y es tipo SOUND
            field_info = next((f for f in tables_dict[table_name]["fields"] if f["name"] == field_name), None)
            if field_info and field_info["type"].upper() == "SOUND":
                tables_dict[table_name]["indexes"].append({
                    "field_name": field_name,
                    "type": "INVERTED INDEX"
                })

    # Agregar índices invertidos si el campo existe
    for table_name, fields in inverted_indexes.items():
        if table_name in tables_dict:
            existing_field_names = {f["name"] for f in tables_dict[table_name]["fields"]}
            for field_name in fields:
                if field_name in existing_field_names:
                    tables_dict[table_name]["indexes"].append({
                        "field_name": field_name,
                        "type": "INVERTED INDEX"
                    })

    output["tables"] = list(tables_dict.values())
    return output

def get_sound_files_info_fast():
    sounds_path = Utils.build_path("sounds")
    supported_extensions = ('.mp3', '.wav', '.flac', '.ogg', '.aac')
    sound_info_list = []

    digit_file_count = 0
    digit_file_limit = 40
    total_sound_files = 0

    for filename in os.listdir(sounds_path):
        if filename.lower().endswith(supported_extensions):
            total_sound_files += 1  # contar todos los archivos válidos

            name_part = os.path.splitext(filename)[0]
            is_six_digit_number = re.fullmatch(r'\d{6}', name_part)

            # si tiene 6 dígitos y ya alcanzamos el límite, lo ignoramos
            if is_six_digit_number:
                if digit_file_count >= digit_file_limit:
                    continue
                digit_file_count += 1

            # procesar el archivo
            file_path = os.path.join(sounds_path, filename)
            try:
                audio = MutagenFile(file_path)
                if audio is not None and audio.info is not None:
                    duration_sec = round(audio.info.length)
                    sound_info_list.append({
                        "name": filename,
                        "duration": duration_sec
                    })
            except Exception as e:
                print(f"Error leyendo metadata de {filename}: {e}")

    sound_info_list.sort(key=lambda x: (re.fullmatch(r'\d{6}', os.path.splitext(x["name"])[0]) is not None, x["name"]))

    return {
        "num_sounds": total_sound_files,
        "file_sounds": sound_info_list
    }


def detect_type(value):
    if isinstance(value, str):
        if value.endswith(".mp3") or value.endswith(".wav"):
            return "SOUND"
        elif len(value) > 100:
            return "TEXT"
        elif len(value) <= 10 and ':' in value:
            return "VARCHAR(10)"  # posible duración
        else:
            return "VARCHAR(100)"
    elif isinstance(value, int):
        return "INT"
    elif isinstance(value, float):
        return "FLOAT"
    else:
        return "UNKNOWN"
    
def execute_consulta(consulta:str):

    start = time.time()

    # Supongamos que esta función ya hace todo lo necesario y te da un QueryResult válido
    """
    query_result:QueryResult=QueryResult(
        success=True,
        message="Consulta ejecutada correctamente.",
        data=pd.DataFrame(rows)
    )
    """
    """
    runVisitor = RunVisitor()
    scanner = Scanner(consulta)
    parser = Parser(scanner)
    program = parser.parse_program()
    query_result: QueryResult = runVisitor.visit_program(program)
    """
    query_result:QueryResult= query_run(consulta)
    end = time.time()

    df = query_result.data

    # Detectar tipos de columnas
    columns_info = []
    for col in df.columns:
        first_valid = df[col].dropna().iloc[0] if not df[col].dropna().empty else ""
        col_type = detect_type(first_valid)
        columns_info.append({
            "field_name": col,
            "type": col_type
        })


    return {
        "columns": columns_info,
        "rows": df.to_dict(orient="records"),
        "message": query_result.message,
        "count_rows": len(df),
        "time_execution": round((end - start) * 1000)
    }


if __name__ == "__main__":
    result = execute_consulta("")
    print(json.dumps(result, indent=4, ensure_ascii=False))
