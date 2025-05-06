# Pasos de implementación del proyecto

## 1. Estructuras de almacenamiento e índices
- Implementar las siguientes estructuras:
  - Sequential File (o AVL File)
  - ISAM (índice estático de 2 niveles con páginas overflow)
  - Extendible Hashing
  - B+ Tree
  - R-Tree (para vectores o datos espaciales)

## 2. Operaciones básicas por estructura
- Implementar en cada estructura:
  - `add(registro)` – Inserción
  - `search(key)` – Búsqueda exacta (puede haber varias coincidencias)
  - `rangeSearch(start, end)` – Búsqueda por rango (no aplica a hashing)
  - `remove(key)` – Eliminación (definir algoritmo por estructura)

## 3. Parser SQL personalizado
- Traducir sentencias SQL personalizadas a llamadas a funciones:
  - `CREATE TABLE` con índice especificado por columna
  - `INSERT INTO ... VALUES (...)`
  - `SELECT * FROM ... WHERE ...`
  - `DELETE FROM ... WHERE ...`
  - `CREATE TABLE ... FROM FILE ... USING INDEX ...`

## 4. Backend en Python
- Usar Flask o FastAPI para:
  - Recibir y ejecutar sentencias del ParserSQL
  - Gestionar archivos, índices y datos
  - Responder con resultados (JSON o estructura clara)

## 5. Soporte a datos multidimensionales
- Usar R-Tree para:
  - Indexar vectores, ubicaciones espaciales, etc.
  - Soportar búsquedas por proximidad o rango espacial

## 6. Interfaz gráfica (opcional pero recomendada)
- Implementar una GUI simple (Python con Tkinter, PyQt, etc.) para:
  - Mostrar resultados de consultas
  - Crear/editar tablas
  - Ejecutar sentencias SQL visualmente

(https://media1.tenor.com/m/jRaSFSY9f78AAAAC/postgresql-heart-locket.gif)