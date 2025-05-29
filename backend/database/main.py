from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import pandas as pd
import json
from fastapi.middleware.cors import CORSMiddleware
import uvicorn  # Importar uvicorn para correr el servidor
from  yarasca import *
from catalog import build_json_structure
import os
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

def parsejson(self, query:str,limit):
    scanner = Scanner(query)
    # scanner.test()
    parser = Parser(scanner, debug=False)
    program = parser.parse_program()
    printVisitor.visit_program(program)
    
    queryresult: QueryResult = execVisitor.visit_program(program)
    
    if queryresult.success:
        df=queryresult.data
        if df is not None:
            df=queryresult.data
            df_limited_rows = df.head(limit) # Obtiene las primeras 10 filas
            query_result = {
                'columns': [{'key': col, 'name': col} for col in df_limited_rows.columns],
                'rows': df_limited_rows.to_dict(orient='records'),
                'count_rows':len(df) 
            }
            return query_result
        else:
            return {
                        'columns': [],
                        'rows': [],
                        "message": "Consulta ejecutada correctamente.",
                        'count_rows':0
                        }
    else:
        return Exception(f"Error en la consulta:")
        
# Ejecutar cualquier consulta (SELECT o no SELECT)
def ejecutar_consulta_sql(query: str, limit: int):
    try:
        scanner = Scanner(query)
        # scanner.test()
        parser = Parser(scanner, debug=False)
        program = parser.parse_program()
        printVisitor.visit_program(program)
        result: QueryResult = execVisitor.visit_program(program)
        return parsejson(query,limit)
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
        base_path = base_path = os.path.join(os.path.dirname(__file__), "tables")  # Carpeta donde están los archivos
        db_name = "MY_DB"

        structure = build_json_structure(base_path, db_name)
        return structure

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener la estructura: {e}")
    

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
