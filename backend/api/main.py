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
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from backend.api.utils_api import *
from mutagen import File as MutagenFile

from backend.database.global_utils import Utils

app = FastAPI(title="DataQuill API", version="1.0.0")

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



# Modelos Pydantic
class QueryRequest(BaseModel):
    consulta: str

class AudioRequest(BaseModel):
    file_sound: str



@app.get("/schema")
async def get_schema():
    """Obtener el esquema de la base de datos"""
    return generate_database_structure()

@app.post("/query")
async def execute_query(query_request: QueryRequest):
    """Ejecutar una consulta SQL"""
    print(query_request.consulta)
    return execute_consulta(query_request.consulta)

@app.get("/audio")
async def get_audio(file_name: str):
    file_path = Utils.build_path("sounds", file_name)
    if not os.path.exists(file_path):
        return {"error": "File not found"}

    return FileResponse(
        path=file_path,
        media_type="audio/mpeg",
        filename=file_name
    )

@app.get("/audio-files")
async def get_audio_files():
    """Obtener lista de archivos de audio"""
    return get_sound_files_info_fast()

@app.post("/upload-audio")
async def upload_audio(file: UploadFile = File(...)):
    supported_extensions = ('.mp3', '.wav', '.ogg')

    if not file.filename.lower().endswith(supported_extensions):
        raise HTTPException(status_code=400, detail="Formato de archivo no soportado")

    try:
        sounds_dir = Utils.build_path("sounds")
        os.makedirs(sounds_dir, exist_ok=True)

        # Ruta final del archivo
        file_path = os.path.join(sounds_dir, file.filename)

        # Guardar el archivo en disco
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Obtener duración con Mutagen
        audio = MutagenFile(file_path)
        if audio is None or audio.info is None:
            raise HTTPException(status_code=400, detail="No se pudo leer metadata del archivo de audio")

        duration = round(audio.info.length)

        return {
            "success": True,
            "file": {
                "name": file.filename,
                "duration": duration
            }
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al subir el archivo: {str(e)}")

@app.get("/")
async def root():
    """Endpoint raíz"""
    return {"message": "DataQuill API funcionando correctamente"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)