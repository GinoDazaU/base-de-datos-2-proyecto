from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import pandas as pd
import json
from fastapi.middleware.cors import CORSMiddleware
import uvicorn  # Importar uvicorn para correr el servidor
from  parser import Parser
from catalog import build_json_structure

# FastAPI App
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Permite cualquier origen
    allow_credentials=True,
    allow_methods=["*"],  # Permite todos los métodos HTTP (GET, POST, etc)
    allow_headers=["*"],  # Permite todas las cabeceras
)
# Modelo de entrada
class ConsultaSQL(BaseModel):
    consulta: str

# Ejecutar cualquier consulta (SELECT o no SELECT)
def ejecutar_consulta_sql(query: str, limit: int):
    try:
        parse=Parser()
        return parse.parsejson(query,limit)
    except Exception as e:
        raise Exception(f"Error en la consulta: {e}")

# Endpoint
@app.post("/consultar/{limit}")
def ejecutar_consulta(entrada: ConsultaSQL,limit:int ):
    try:
        return ejecutar_consulta_sql(entrada.consulta, limit)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    

@app.get("/estructura")
def obtener_estructura_bd():
    try:
        base_path = "backend/database/tables"  # Carpeta donde están los archivos
        db_name = "MY_DB"

        structure = build_json_structure(base_path, db_name)
        return structure

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener la estructura: {e}")
    

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
