# Proyecto 2: Mapeando el Caos  
## Indexación y Organización de Datos No Estructurados para Datos Multimedia

---

## 1. Introducción

Breve descripción del proyecto, motivación y objetivos generales.

- ¿Qué problema resuelve?
- ¿Qué funcionalidades principales tiene la aplicación?
- ¿Qué tipo de datos utiliza (texto, imágenes, audio)?
- ¿Qué tecnologías se emplean?

---

## 2. Arquitectura del Sistema

Diagrama arquitectónico general del sistema, describiendo los principales módulos:

- Preprocesamiento de datos
- Construcción de índices
- Módulo de consulta
- Interfaz de usuario
- Almacenamiento

Incluir un diagrama de flujo o arquitectura.

---

## 3. Índice Invertido Textual

### 3.1. Preprocesamiento

- Tokenización  
- Eliminación de stopwords  
- Stemming  
- Normalización  

### 3.2. Construcción del Índice

- Modelo TF-IDF  
- Cálculo y almacenamiento de normas  
- SPIMI (Single-pass in-memory indexing)  
- Explicación del algoritmo y su implementación (puede incluir pseudocódigo o diagrama)

### 3.3. Consulta

- Consulta libre en lenguaje natural  
- Similitud de coseno  
- Recuperación Top-K sin cargar todo el índice en memoria  

---

## 4. Indexación de Datos Multimedia

### 4.1. Extracción de Características

- Descriptores utilizados (e.g., MFCC para audio, ResNet50 para imágenes)  
- Librerías empleadas  

### 4.2. Construcción del Diccionario Visual / Acústico

- K-Means sobre los descriptores locales  
- Visual/acoustic words  
- Representación de cada objeto como histograma  

### 4.3. Búsqueda KNN Secuencial

- TF-IDF sobre histogramas  
- Similitud de coseno  
- Recuperación eficiente con heap (Top-K)

### 4.4. Búsqueda KNN con Indexación Invertida

- Estructura del índice invertido sobre visual/acoustic words  
- Adaptación del modelo textual a dominio multimedia  
- Funcionamiento y optimización

---

## 5. Interfaz de Usuario

### 5.1. FrontEnd para Búsqueda Textual

- Sintaxis de consulta (tipo SQL o personalizada)  
- Ejemplo de uso  
- Presentación de resultados  
- Medición de tiempo de respuesta  

### 5.2. FrontEnd para Consultas Multimedia

- Carga de imagen o audio de consulta  
- Resultados visuales con metadatos  
- Asociación con resultados textuales  
- Ejemplo de uso y respuesta

---

## 6. Evaluación y Comparación de Desempeño

### 6.1. Comparación de Búsqueda en Texto

- Consultas equivalentes entre nuestro sistema y PostgreSQL  
- Tiempos de respuesta, precisión de resultados  
- Tecnologías usadas por PostgreSQL (GIN, GiST, ts_rank, etc.)

### 6.2. Comparación en Búsqueda Multimedia

- Comparación entre KNN secuencial y KNN con índice invertido  
- Tiempo de ejecución y escalabilidad  
- Comparación con herramientas externas (pgVector, Faiss)  
- Discusión sobre la maldición de la dimensionalidad

### 6.3. Resultados

- Tablas comparativas  
- Gráficos de rendimiento  
- Análisis crítico

---

## 7. Datasets Utilizados

- Nombre del dataset  
- Fuente (Kaggle, GitHub, etc.)  
- Descripción del contenido  
- Número de registros / imágenes / audios

---

## 9. Repositorio y Ejecución

### 9.1. Requisitos del Sistema

- Lenguaje / versiones  
- Librerías / dependencias  

### 9.2. Instrucciones de Ejecución

```bash
# Clonar el repositorio
git clone https://github.com/usuario/proyecto2.git
cd proyecto2

# Instalar dependencias
pip install -r requirements.txt

# Ejecutar la aplicación
python app.py
