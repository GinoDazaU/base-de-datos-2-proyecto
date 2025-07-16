from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List, Dict, Any
import json
import os
import time
from pathlib import Path
import shutil
import sys
from catalog import *

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


app = FastAPI(title="DataQuill API", version="1.0.0")

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuración de directorios
AUDIO_DIR = Path("audio_files")
AUDIO_DIR.mkdir(exist_ok=True)

# Modelos Pydantic
class QueryRequest(BaseModel):
    consulta: str

class AudioRequest(BaseModel):
    file_sound: str

# Datos mock para el schema
SCHEMA_DATA = {
    "db": "Sales DB",
    "tables": [
        {
            "table_name": "songs",
            "fields": [
                {"name": "id", "type": "INT", "is_primary_key": True},
                {"name": "title", "type": "VARCHAR(100)", "is_primary_key": False},
                {"name": "sound_file", "type": "SOUND", "is_primary_key": False},
                {"name": "artist", "type": "VARCHAR(100)", "is_primary_key": False},
                {"name": "duration", "type": "VARCHAR(10)", "is_primary_key": False},
                {"name": "genre", "type": "VARCHAR(50)", "is_primary_key": False},
                {"name": "url", "type": "VARCHAR(300)", "is_primary_key": False}
            ],
            "indexes": [
                {"field_name": "id", "type": "btree"}
            ]
        }
    ]
}

# Datos mock para las consultas
QUERY_RESULT_DATA = {
    "columns": [
        {"field_name": "id", "type": "INT"},
        {"field_name": "title", "type": "VARCHAR(100)"},
        {"field_name": "sound_file", "type": "SOUND"},
        {"field_name": "artist", "type": "VARCHAR(100)"},
        {"field_name": "duration", "type": "VARCHAR(10)"},
        {"field_name": "genre", "type": "VARCHAR(50)"},
        {"field_name": "description", "type": "TEXT"}
    ],
    "rows": [
        {
            "id": 1,
            "title": "Bohemian Rhapsody",
            "sound_file": "0000001.mp3",
            "artist": "Queen",
            "duration": "5:55",
            "genre": "Rock",
            "description": "Una obra maestra del rock progresivo que combina elementos de ópera, balada y hard rock. Escrita por Freddie Mercury, es considerada una de las mejores canciones de todos los tiempos por su estructura única y complejidad musical."
        },
        {
            "id": 2,
            "title": "Imagine",
            "sound_file": "0000002.mp3",
            "artist": "John Lennon",
            "duration": "3:03",
            "genre": "Pop",
            "description": "Una canción icónica sobre la paz mundial y la unidad. John Lennon invita a imaginar un mundo sin divisiones religiosas, políticas o nacionales, convirtiéndose en un himno para la paz."
        },
        {
            "id": 3,
            "title": "Hotel California",
            "sound_file": "0000003.mp3",
            "artist": "Eagles",
            "duration": "6:30",
            "genre": "Rock",
            "description": "Una enigmática canción que narra la historia de un viajero que se detiene en un lujoso pero misterioso hotel del que aparentemente no puede escapar. Famosa por su memorable solo de guitarra final."
        }
    ],
    "message": "Consulta ejecutada correctamente.",
    "count_rows": 3,
    "time_execution": 150
}

# Datos mock para archivos de audio
AUDIO_FILES_DATA = {
    "file_sounds": [
        {"name": "0000001.mp3", "duration": 355},
        {"name": "0000002.mp3", "duration": 183},
        {"name": "0000003.mp3", "duration": 390}
    ]
}

# Endpoints

@app.get("/schema")
async def get_schema():
    """Obtener el esquema de la base de datos"""
    return generate_database_structure()

@app.post("/query")
async def execute_query(query_request: QueryRequest):
    """Ejecutar una consulta SQL"""
    # Simular tiempo de ejecución
    time.sleep(0.1)
    
    # Simular diferentes respuestas basadas en la consulta
    consulta = query_request.consulta.lower()
    
    if "error" in consulta:
        raise HTTPException(status_code=400, detail="Error en la consulta SQL")
    
    return QUERY_RESULT_DATA

@app.post("/audio")
async def get_audio_file(audio_request: AudioRequest):
    """Obtener un archivo de audio"""
    file_path = AUDIO_DIR / audio_request.file_sound
    
    # Si el archivo no existe, crear uno temporal para la demo
    if not file_path.exists():
        # Crear un archivo de audio vacío para la demo
        file_path.touch()
    
    # En producción, aquí se retornaría el archivo real
    return FileResponse(
        path=file_path,
        media_type="audio/mpeg",
        filename=audio_request.file_sound
    )

@app.get("/audio-files")
async def get_audio_files():
    """Obtener lista de archivos de audio"""
    return AUDIO_FILES_DATA

@app.post("/upload-audio")
async def upload_audio(file: UploadFile = File(...)):
    """Subir un archivo de audio"""
    if not file.filename.endswith(('.mp3', '.wav', '.ogg')):
        raise HTTPException(status_code=400, detail="Formato de archivo no soportado")
    
    # Guardar el archivo
    file_path = AUDIO_DIR / file.filename
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # Calcular duración simulada
    duration = 180  # 3 minutos por defecto
    
    # Agregar a la lista de archivos
    AUDIO_FILES_DATA["file_sounds"].append({
        "name": file.filename,
        "duration": duration
    })
    
    return {"message": "Archivo subido correctamente", "filename": file.filename}

@app.get("/")
async def root():
    """Endpoint raíz"""
    return {"message": "DataQuill API funcionando correctamente"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)