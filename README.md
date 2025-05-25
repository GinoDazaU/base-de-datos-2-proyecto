<meta charset="UTF-8">

<h1 align="center">Mini DataBase Manager</h3>

---

<h3 align="center">📚 Curso: Database II 📚</h3>

<div align="center">
    <img src="./images/01.png" alt="Proveedores Cloud" style="width: 100%;">
</div>

<h3>👨‍💻 Integrantes</h3>

<div align="center">
    <img src="./images/03.png" alt="Proveedores Cloud" style="width: 100%;">
</div>


## Tabla de Contenidos
- [1. Introducción](#1-introducción)
  - [1.1. Objetivo del Proyecto](#11-objetivo-del-proyecto)
  - [1.2. Descripción de la Aplicación](#12-descripción-de-la-aplicación)
  - [1.3. Resultados Esperados](#13-resultados-esperados)
- [2. Técnicas de Indexación Utilizadas](#2-técnicas-de-indexación-utilizadas)
  - [2.1. Descripción Breve de Técnicas](#21-descripción-breve-de-técnicas)
  - [2.2. Algoritmos de Inserción, Eliminación y Búsqueda](#22-algoritmos-de-inserción-eliminación-y-búsqueda)
  - [2.3. Análisis Comparativo Teórico de Técnicas](#23-análisis-comparativo-teórico-de-técnicas)
  - [2.4. Optimización del Manejo de Memoria Secundaria](#24-optimización-del-manejo-de-memoria-secundaria)
  - [2.5. Explicación del Parser SQL](#25-explicación-del-parser-sql)
- [3. Resultados Experimentales y Análisis](#3-resultados-experimentales-y-análisis)
  - [3.1. Cuadro/Gráfico Comparativo de Desempeño](#31-cuadrográfico-comparativo-de-desempeño)
  - [3.2. Métricas de Desempeño (Accesos a Disco y Tiempo)](#32-métricas-de-desempeño-accesos-a-disco-y-tiempo)
  - [3.3. Discusión y Análisis de Resultados](#33-discusión-y-análisis-de-resultados)
- [4. Pruebas de Uso y Presentación de la Aplicación](#4-pruebas-de-uso-y-presentación-de-la-aplicación)
  - [4.1. Presentación de Pruebas en Interfaz Gráfica](#41-presentación-de-pruebas-en-interfaz-gráfica)
  - [4.2. Evidencia del Aporte de Índices](#42-evidencia-del-aporte-de-índices)
  - [4.3. Video Demostrativo de Funcionalidad](#43-video-demostrativo-de-funcionalidad)
  - [](#)
- [🔗 Referencias](#-referencias)
- [Oveview - Pasos de implementación del proyecto](#oveview---pasos-de-implementación-del-proyecto)

  
¡Bienvenido al proyecto **[DataQuill]**! Este repositorio alberga **[descripción breve del proyecto]**, un sistema que explora y optimiza el manejo de datos a través de diversas técnicas de indexación.

---

# 1. Introducción

## 1.1. Objetivo del Proyecto

El objetivo principal de este proyecto es **diseñar e implementar un sistema que demuestre la eficacia de diferentes técnicas de indexación de archivos** para optimizar operaciones de bases de datos. Buscamos crear una aplicación donde se pueda visualizar claramente cómo la elección de una técnica de indexación impacta directamente en el rendimiento de la inserción, búsqueda y eliminación de datos.

## 1.2. Descripción de la Aplicación

Hemos desarrollado una **aplicación interesante e interactiva** (Interfaz Gráfica Amigable e Intuitiva) que sirve como entorno de prueba para las técnicas de indexación. Esta aplicación permite a los usuarios **[describir brevemente qué puede hacer el usuario en la aplicación, ej. cargar grandes volúmenes de datos, realizar consultas, visualizar estructuras de índice]**. La aplicación está diseñada para ser un ejemplo práctico de cómo las técnicas de indexación pueden combinarse y aplicarse en un escenario real, permitiendo la comparación directa de su desempeño.

## 1.3. Resultados Esperados

Al finalizar este proyecto, esperamos obtener los siguientes resultados:

* Una **aplicación funcional** que combine múltiples técnicas de indexación de archivos.
* **Demostraciones claras y cuantificables** del impacto de cada técnica de indexación en las operaciones de inserción, búsqueda y eliminación.
* **Análisis de desempeño** que muestre la optimización en términos de accesos a memoria secundaria y tiempo de ejecución.
* Un **ParserSQL robusto** capaz de interpretar y ejecutar comandos SQL relevantes para las operaciones indexadas.
* Una **interfaz gráfica intuitiva** que facilite la interacción y la visualización de los resultados.



# 2. Técnicas de Indexación Utilizadas
<details>
<summary><strong>Ver más</strong></summary>

## 2.1. Descripción Breve de Técnicas
<details>
<summary><strong>Ver más</strong></summary>

En este proyecto, hemos implementado y evaluado las siguientes técnicas de indexación de archivos:

* **[Técnica 1, ej., Árbol B+]**: [Breve descripción de la técnica, sus principios y por qué fue elegida, ej., "estructura de árbol balanceada que permite búsquedas, inserciones y eliminaciones eficientes, ideal para datos en disco debido a su alta factor de ramificación."].
* **[Técnica 2, ej., Hashing Extensible]**: [Breve descripción de la técnica, sus principios y por qué fue elegida, ej., "método de hashing dinámico que se adapta al crecimiento de datos, reduciendo colisiones y manteniendo un buen rendimiento de búsqueda y actualización."].
* **[Técnica 3, opcional, ej., Índice Secuencial Simple / B-Tree]**: [Breve descripción si aplica. Si solo usaste 2 técnicas principales, puedes omitir esta o expandir las anteriores].

</details>

## 2.2. Algoritmos de Inserción, Eliminación y Búsqueda

<details>
<summary><strong>Ver más</strong></summary>

Para cada técnica de indexación implementada, hemos desarrollado y optimizado los algoritmos fundamentales:

* **Inserción**: Se explica cómo se añade un nuevo registro al índice, detallando los pasos lógicos y las operaciones de disco involucradas.
    * **[Insertar aquí el código o la ruta a los gráficos/diagramas que ilustren el proceso de inserción para cada técnica. Ej: `![Diagrama de Inserción B+](./docs/insercion_bplus.png)`]**
* **Eliminación**: Se describe el proceso para remover un registro del índice, incluyendo el manejo de espacio liberado y la reorganización de la estructura.
    * **[Insertar aquí el código o la ruta a los gráficos/diagramas que ilustren el proceso de eliminación para cada técnica. Ej: `![Diagrama de Eliminación Hashing](./docs/eliminacion_hashing.png)`]**
* **Búsqueda**: Se detalla cómo se localiza un registro utilizando la estructura del índice, enfatizando la eficiencia de las operaciones de lectura en disco.
    * **[Insertar aquí el código o la ruta a los gráficos/diagramas que ilustren el proceso de búsqueda para cada técnica. Ej: `![Diagrama de Búsqueda B+](./docs/busqueda_bplus.png)`]**

</details>

## 2.3. Análisis Comparativo Teórico de Técnicas
<details>
<summary><strong>Ver más</strong></summary>

Hemos realizado un **análisis comparativo teórico** de las técnicas implementadas, centrándonos en los **accesos a memoria secundaria** (operaciones de I/O a disco duro) para las operaciones clave. Este análisis busca predecir el comportamiento de cada técnica en diferentes escenarios de datos:

* **Inserción**: [Comparación teórica de I/O para inserciones, ej., "El Árbol B+ tiende a requerir `log_f(N)` accesos en el peor caso, mientras que el Hashing Extensible apunta a un acceso promedio constante."].
* **Búsqueda**: [Comparación teórica de I/O para búsquedas, ej., "Para búsquedas exactas, el Hashing es superior en promedio, pero el B+ es más consistente y mejor para búsquedas de rango."].
* **Eliminación**: [Comparación teórica de I/O para eliminaciones, ej., "La eliminación puede ser compleja en ambos, pero el B+ mantiene su balance, mientras que el Hashing puede requerir reestructuración de cubetas."].

</details>

## 2.4. Optimización del Manejo de Memoria Secundaria
<details>
<summary><strong>Ver más</strong></summary>

El código del proyecto ha sido **cuidadosamente optimizado** para el manejo de memoria secundaria. Esto incluye:

* **Paginación eficiente**: Implementación de un gestor de bloques que minimiza las lecturas y escrituras a disco, cargando solo los bloques necesarios en memoria RAM.
* **Buffer Pooling**: Gestión de un pool de buffers para reutilizar bloques de memoria, reduciendo la necesidad de accesos a disco redundantes.
* **[Otras optimizaciones, ej., Uso de punteros a disco, estrategias de caché, etc.]**
</details>

## 2.5. Explicación del Parser SQL
<details>
<summary><strong>Ver más</strong></summary>
Para permitir la interacción con las estructuras de datos indexadas, hemos desarrollado un **Parser SQL** personalizado. Este parser es responsable de:

* **Análisis Léxico y Sintáctico**: Interpretar las cadenas de comandos SQL de entrada.
* **Soporte de Comandos**: Actualmente, el parser soporta operaciones SQL como:
    * `` `INSERT INTO ... VALUES (...)` ``
    * `` `SELECT ... FROM ... WHERE ...` `` (con filtros simples y de rango)
    * `` `DELETE FROM ... WHERE ...` ``
    * **[Añadir otros comandos si son soportados, ej., `CREATE TABLE`, `CREATE INDEX`]**
* **Integración con Índices**: El parser traduce los comandos SQL en llamadas a los algoritmos de inserción, búsqueda y eliminación de las técnicas de indexación implementadas, asegurando que las operaciones se beneficien de la indexación cuando corresponda.

</details>

</details>


# 3. Resultados Experimentales y Análisis
<details>
<summary><strong>Ver más</strong></summary>

## 3.1. Cuadro/Gráfico Comparativo de Desempeño
<details>
<summary><strong>Ver más</strong></summary>

Hemos realizado pruebas exhaustivas para evaluar el desempeño de cada técnica de indexación bajo diferentes escenarios y volúmenes de datos. Los resultados se presentan en los siguientes **cuadros y gráficos comparativos**:

* **[Insertar aquí Cuadro/Gráfico 1]**: Desempeño de **Inserción** (Comparación de accesos a disco y tiempo de ejecución vs. número de registros).
    ```markdown
    ![Gráfico de Inserción](./assets/grafico_insercion.png)

    | Registros | Técnica 1 (I/O) | Técnica 1 (Tiempo ms) | Técnica 2 (I/O) | Técnica 2 (Tiempo ms) |
    |-----------|-----------------|-----------------------|-----------------|-----------------------|
    | 1000      | 50              | 10                    | 30              | 5                     |
    | 10000     | 200             | 50                    | 120             | 20                    |
    ```
* **[Insertar aquí Cuadro/Gráfico 2]**: Desempeño de **Búsqueda** (Comparación de accesos a disco y tiempo de ejecución vs. número de registros / selectividad de la consulta).
    ```markdown
    ![Gráfico de Búsqueda](./assets/grafico_busqueda.png)
    ```
* **[Insertar aquí Cuadro/Gráfico 3]**: Desempeño de **Eliminación** (Comparación de accesos a disco y tiempo de ejecución vs. número de registros).
    ```markdown
    ![Gráfico de Eliminación](./assets/grafico_eliminacion.png)
    ```
</details>

## 3.2. Métricas de Desempeño (Accesos a Disco y Tiempo)
<details>
<summary><strong>Ver más</strong></summary>

Para cada prueba, se monitorearon y registraron dos métricas clave:

* **Total de Accesos a Disco Duro (Read & Write)**: Contabilizamos el número total de operaciones de lectura y escritura realizadas en la memoria secundaria. Esta métrica es crucial para evaluar la eficiencia de I/O de cada algoritmo.
* **Tiempo de Ejecución (en milisegundos)**: Medimos el tiempo total que tomó cada operación (inserción, búsqueda, eliminación) para completarse, ofreciendo una perspectiva del rendimiento percibido por el usuario.

</details>

## 3.3. Discusión y Análisis de Resultados
<details>
<summary><strong>Ver más</strong></summary>

Los resultados experimentales validan **[confirmar o refutar las hipótesis iniciales / análisis teórico]**. Observamos que:

* **[Discusión para Inserción]**: Ej., "Como se predijo, el Hashing Extensible mostró un rendimiento superior en inserciones aleatorias debido a su acceso directo, mientras que el B+ mantuvo un rendimiento consistente pero con más I/O a gran escala."
* **[Discusión para Búsqueda]**: Ej., "Para búsquedas de rango, el Árbol B+ superó significativamente al Hashing. En búsquedas exactas, ambos fueron rápidos, pero el Hashing demostró una ligera ventaja para grandes volúmenes de datos."
* **[Discusión para Eliminación]**: Ej., "La eliminación en el Hashing Extensible fue eficiente, pero en ciertos puntos de inflexión (cuando la cubeta se dividía), se observaron picos en los accesos a disco. El B+ mantuvo una curva más suave."
* **[Conclusiones Generales]**: Ej., "La optimización del manejo de memoria secundaria fue fundamental para minimizar los accesos a disco en todas las técnicas, confirmando la importancia de un buen diseño de buffers."
</details>

</details>

# 4. Pruebas de Uso y Presentación de la Aplicación
<details>
<summary><strong>Ver más</strong></summary>

## 4.1. Presentación de Pruebas en Interfaz Gráfica
<details>
<summary><strong>Ver más</strong></summary>

La aplicación cuenta con una **interfaz gráfica de usuario (GUI) amigable e intuitiva**, diseñada para facilitar la interacción y la visualización del funcionamiento de las técnicas de indexación. Las pruebas de uso incluyen:

* **Creación y carga de datasets**: Funcionalidad para importar y generar grandes volúmenes de datos para las pruebas.
* **Ejecución de operaciones**: Botones y campos para ejecutar inserciones, búsquedas y eliminaciones.
* **Visualización de resultados**: Paneles donde se muestran en tiempo real las métricas de desempeño (accesos a disco, tiempo) para cada operación y técnica seleccionada.
* **Representación de la estructura del índice**: **[Opcional, pero muy útil: Si la GUI muestra alguna representación visual de cómo crece o se reorganiza el índice (ej., un árbol B+ visualizado), menciónalo aquí]**.

</details>

## 4.2. Evidencia del Aporte de Índices

<details>
<summary><strong>Ver más</strong></summary>

Durante las pruebas de uso, la aplicación hace **evidente el aporte de los índices** al comparar el desempeño con y sin su uso (o entre diferentes tipos de índices). Se mostrarán escenarios donde:

* Las **consultas con índice** se resuelven en milisegundos, mientras que sin índice toman segundos o más en grandes datasets.
* Las **operaciones de inserción/eliminación** mantienen un rendimiento aceptable incluso con un alto volumen de datos gracias a la estructura del índice.
* **[Ejemplo específico de demostración]**: Ej., "Una búsqueda de un registro específico en 1 millón de elementos tarda `X` ms con un índice, y `Y` ms sin él, donde `Y` es significativamente mayor."

</details>

## 4.3. Video Demostrativo de Funcionalidad

Hemos preparado un **video demostrativo** que muestra la funcionalidad completa de la aplicación, incluyendo:

* El proceso de carga de datos.
* La ejecución de operaciones de inserción, búsqueda y eliminación.
* La visualización en tiempo real de las métricas de desempeño.
* La interfaz gráfica interactiva.
* **[Cualquier característica destacada que quieras mostrar]**.

Puedes ver el video demo aquí: **[ENLACE A TU VIDEO DE DEMOSTRACIÓN (Youtube, Google Drive, etc.)]**
</details>
---

# 🔗 Referencias

* **[Referencia 1]**: Título del libro/artículo, Autor(es), Editorial/Conferencia, Año. Ej., "Database System Concepts", Abraham Silberschatz, Henry F. Korth, S. Sudarshan, McGraw-Hill Education, 2019.
* **[Referencia 2]**: Enlace a documentación relevante, otro repositorio, etc.
* **[Referencia 3]**: ... y así sucesivamente.

---

# Oveview - Pasos de implementación del proyecto
<details>
<summary><strong>Ver más</strong></summary>

</h2>1. Estructuras de almacenamiento e índices</h2> 
- Implementar las siguientes estructuras:
  - Sequential File (o AVL File)
  - ISAM (índice estático de 2 niveles con páginas overflow)
  - Extendible Hashing
  - B+ Tree
  - R-Tree (para vectores o datos espaciales)

</h2>2. Operaciones básicas por estructura</h2> 

- Implementar en cada estructura:
  - `add(registro)` – Inserción
  - `search(key)` – Búsqueda exacta (puede haber varias coincidencias)
  - `rangeSearch(start, end)` – Búsqueda por rango (no aplica a hashing)
  - `remove(key)` – Eliminación (definir algoritmo por estructura)

</h2>3. Parser SQL personalizado</h2> 

- Traducir sentencias SQL personalizadas a llamadas a funciones:
  - `CREATE TABLE` con índice especificado por columna
  - `INSERT INTO ... VALUES (...)`
  - `SELECT * FROM ... WHERE ...`
  - `DELETE FROM ... WHERE ...`
  - `CREATE TABLE ... FROM FILE ... USING INDEX ...`

</h2>4. Backend en Python</h2> 

- Usar Flask o FastAPI para:
  - Recibir y ejecutar sentencias del ParserSQL
  - Gestionar archivos, índices y datos
  - Responder con resultados (JSON o estructura clara)

</h2>5. Soporte a datos multidimensionales</h2> 

- Usar R-Tree para:
  - Indexar vectores, ubicaciones espaciales, etc.
  - Soportar búsquedas por proximidad o rango espacial

</h2>6. Interfaz gráfica (opcional pero recomendada)</h2> 

- Implementar una GUI simple (Python con Tkinter, PyQt, etc.) para:
  - Mostrar resultados de consultas
  - Crear/editar tablas
  - Ejecutar sentencias SQL visualmente
</details>

![](https://media1.tenor.com/m/jRaSFSY9f78AAAAC/postgresql-heart-locket.gif)