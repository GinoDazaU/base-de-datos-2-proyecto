<meta charset="UTF-8">

<h1 align="center">Mini DataBase Manager</h3>

---

<h3 align="center">📚 Curso: Database II 📚</h3>

<div align="center">
    <img src="./images/01.png" alt="Proveedores Cloud" style="width: 100%;">
</div>

<h3>👨‍💻 Integrantes</h3>

<div style="display: flex; gap: 1rem; flex-wrap: wrap;">

  <div style="display: flex; flex-direction: column; align-items: center; border: 1px solid #ccc; border-radius: 12px; width: 180px; padding: 1rem; box-shadow: 0 2px 5px rgba(0,0,0,0.1);">
    <img src="./images/02.png" alt="a" style="width: 100px; height: 100px; border-radius: 50%; object-fit: cover; margin-bottom: 0.5rem;">
    <div style="text-align: center;">
      <strong>Casquino Paz, Daniel Ignacio</strong>
    </div>    
  </div>

  <div style="display: flex; flex-direction: column; align-items: center; border: 1px solid #ccc; border-radius: 12px; width: 180px; padding: 1rem; box-shadow: 0 2px 5px rgba(0,0,0,0.1);">
    <img src="./images/02.png" alt="b" style="width: 100px; height: 100px; border-radius: 50%; object-fit: cover; margin-bottom: 0.5rem;">
      <div style="text-align: center;">
        <strong>Daza Yalta, Gino Jesús</strong>
      </div>  
  </div>

  <div style="display: flex; flex-direction: column; align-items: center; border: 1px solid #ccc; border-radius: 12px; width: 180px; padding: 1rem; box-shadow: 0 2px 5px rgba(0,0,0,0.1);">
    <img src="./images/02.png" alt="c" style="width: 100px; height: 100px; border-radius: 50%; object-fit: cover; margin-bottom: 0.5rem;">
    <div style="text-align: center;">
      <strong>Garcia Calle, Renato</strong>
    </div>    
  </div>

  <div style="display: flex; flex-direction: column; align-items: center; border: 1px solid #ccc; border-radius: 12px; width: 180px; padding: 1rem; box-shadow: 0 2px 5px rgba(0,0,0,0.1);">
    <img src="./images/02.png" alt="d" style="width: 100px; height: 100px; border-radius: 50%; object-fit: cover; margin-bottom: 0.5rem;">
    <div style="text-align: center;">
      <strong>Huaylla Huillca, Jean Piero</strong>
    </div>    
  </div>

  <div style="display: flex; flex-direction: column; align-items: center; border: 1px solid #ccc; border-radius: 12px; width: 180px; padding: 1rem; box-shadow: 0 2px 5px rgba(0,0,0,0.1);">
    <img src="./images/02.png" alt="e" style="width: 100px; height: 100px; border-radius: 50%; object-fit: cover; margin-bottom: 0.5rem;">
    <div style="text-align: center;">
      <strong>Niño Castañeda, Jesús Valentín</strong>
    </div>
  </div>

</div>

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

![](https://media1.tenor.com/m/jRaSFSY9f78AAAAC/postgresql-heart-locket.gif)