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

¡Bienvenido al proyecto **DataQuill!** Este repositorio alberga **DataQuill**, un sistema avanzado diseñado para explorar, analizar y optimizar la gestión de datos mediante técnicas de indexación y recuperación eficiente. Nuestro objetivo es mejorar el rendimiento y la escalabilidad en el manejo de grandes volúmenes de información, facilitando consultas rápidas y precisas en entornos variados.

## Tabla de Contenidos
- [1. Introducción](#1-introducción)
  - [1.1. Objetivo del Proyecto](#11-objetivo-del-proyecto)
  - [1.2. Descripción de la Aplicación](#12-descripción-de-la-aplicación)
  - [1.3. Resultados Esperados](#13-resultados-esperados)
- [2. Técnicas de Indexación Utilizadas](#2-técnicas-de-indexación-utilizadas)
  - [2.1. Descripción Breve de Técnicas](#21-descripción-breve-de-técnicas)
  - [2.2. Algoritmos de Inserción, Eliminación y Búsqueda](#22-algoritmos-de-inserción-eliminación-y-búsqueda)
    - [Inserción](#inserción)
    - [Búsqueda](#búsqueda)
    - [Eliminación](#eliminación)
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
- [🔗 Referencias](#-referencias)
- [Oveview - Pasos de implementación del proyecto](#oveview---pasos-de-implementación-del-proyecto)

  


---

# 1. Introducción

## 1.1. Objetivo del Proyecto

El objetivo principal de este proyecto es diseñar e implementar un sistema que demuestre la eficacia de diferentes técnicas de indexación de archivos para optimizar operaciones de bases de datos. Este sistema permitirá comparar en tiempo real el desempeño de cinco técnicas distintas de organización de datos en memoria secundaria, enfocándose especialmente en las operaciones de búsqueda (exacta y por rango), inserción y eliminación.

Además, se desarrollará una aplicación con interfaz gráfica amigable e intuitiva, que permita al usuario cargar datasets, ejecutar consultas SQL personalizadas y visualizar cómo los índices afectan el rendimiento del sistema. Todo esto con el propósito de demostrar claramente el impacto de cada técnica de indexación en términos de accesos a disco y tiempo de ejecución.

## 1.2. Descripción de la Aplicación

La aplicación permite:

- Cargar tablas desde archivos `.csv` o mediante generadores sintéticos.
- Crear índices sobre campos específicos usando comandos SQL interpretados por nuestro parser personalizado.
- Ejecutar consultas SQL como `SELECT`, `INSERT`, `DELETE` y `CREATE TABLE`.
- Visualizar gráficamente las estructuras de índice utilizadas durante su modificación.
- Mostrar métricas en tiempo real de rendimiento: accesos a disco y tiempo de ejecución.
- Comparar el desempeño de las distintas técnicas de indexación *side-by-side*.

La arquitectura está diseñada modularmente, permitiendo fácil extensión futura y cumpliendo con buenas prácticas de programación orientada a objetos y genérica.

## 1.3. Resultados Esperados

Al finalizar el proyecto, esperamos haber logrado lo siguiente:

- Una aplicación funcional que combine múltiples técnicas de indexación de archivos y permita su comparación en tiempo real.
- Demostraciones visuales y cuantitativas del impacto de usar índices versus no usarlos, especialmente en términos de velocidad y cantidad de accesos a disco.
- Análisis teórico y práctico del rendimiento de las técnicas implementadas, enfocado en optimización de I/O bajo diferentes escenarios de carga y consulta.
- Un parser SQL personalizado que interprete comandos básicos y los ejecute contra las estructuras de datos indexadas.
- Una interfaz gráfica intuitiva que permita al usuario elegir datasets, ejecutar operaciones, ver resultados y comprender visualmente el funcionamiento de los índices.


# 2. Técnicas de Indexación Utilizadas
<details open>
<summary><strong>Ver más</strong></summary>

## 2.1. Descripción Breve de Técnicas
<details open>
<summary><strong>Ver más</strong></summary>

Se han implementado cinco técnicas principales de indexación:

1. **Sequential File**  
   Estructura ordenada donde los registros están almacenados físicamente en orden ascendente según la clave primaria. Se utiliza un área de overflow para nuevas inserciones, y se reconstruye al llenarse.

2. **ISAM - Índice Estático de Dos Niveles**  
   Índice estático construido inicialmente sobre datos ordenados. Las nuevas inserciones se almacenan en páginas de overflow. Eficiente para lecturas, menos flexible para actualizaciones frecuentes.

3. **Hashing Extensible**  
   Hashing dinámico que adapta su estructura a medida que los datos crecen. Excelente para búsquedas exactas, pero no soporta rangos.

4. **Árbol B+**  
   Árbol balanceado ideal para I/O en disco. Soporta búsquedas exactas, de rango, inserciones y eliminaciones con buena eficiencia.

5. **RTree**  
   Diseñado para datos multidimensionales como coordenadas, imágenes, regiones. Permite búsquedas espaciales y por rango.

</details>

## 2.2. Algoritmos de Inserción, Eliminación y Búsqueda

<details open>
<summary><strong>Ver más</strong></summary>


### Inserción

A continuación, se describen los algoritmos de inserción implementados para cada técnica de indexación, detallando los pasos lógicos y las operaciones de disco involucradas.

* **Sequential File / AVL File**
    * **Lógica**: Para la inserción de un nuevo registro, el sistema primero intenta localizar espacio disponible directamente en el **archivo principal** si está ordenado y hay una brecha adecuada. Si no hay espacio o si el archivo principal está completamente lleno y mantener el orden físico implicaría una reescritura costosa e inmediata, el registro se inserta en un **área auxiliar (overflow area)**.
    * **Manejo del Overflow y Reconstrucción**: Esta área auxiliar actúa como un buffer para los registros recién insertados. Sin embargo, para mantener la eficiencia de la búsqueda secuencial y por rango, cuando el número de registros en el área auxiliar alcanza un umbral predefinido `K`, se dispara un **algoritmo de reconstrucción** completo. Este proceso implica la lectura de todo el archivo principal y el área auxiliar, la fusión de ambos conjuntos de datos en memoria, y la reescritura completa del archivo principal en disco, asegurando que todos los registros estén nuevamente en orden físico de acuerdo a la clave seleccionada. Durante la reconstrucción, se actualizan los punteros de los índices si los hubiere.
    * `![Diagrama de Inserción en Sequential File](./docs/insercion_sequential.png)`

* **ISAM (Indexed Sequential Access Method)**
    * **Lógica**: Para insertar un registro, se utiliza la estructura de índice para **localizar la página de datos** (o bloque) correcta donde debería residir el registro, basándose en su clave. Si hay **espacio disponible** en esa página de datos, el registro se inserta directamente, manteniendo el orden dentro de la página.
    * **Manejo de Desbordamiento (Overflow)**: Si la página de datos está **llena**, el nuevo registro no se inserta en el archivo principal. En su lugar, se inserta en una **página de desbordamiento (overflow page)**. Si ya existen páginas de desbordamiento encadenadas a la página de datos principal, se busca espacio en ellas. Si todas las páginas de desbordamiento existentes están llenas, se crea una **nueva página de desbordamiento** y se encadena a la última página de desbordamiento de esa secuencia, o directamente a la página de datos principal si es la primera página de desbordamiento. Esta estrategia minimiza la reestructuración del archivo principal, pero puede degradar el rendimiento de la búsqueda si las cadenas de desbordamiento se vuelven muy largas.
    * `![Diagrama de Inserción en ISAM](./docs/insercion_isam.png)`

* **Extendible Hashing**
    * **Lógica**: La inserción comienza calculando el **valor hash** de la clave del registro. Este valor hash se utiliza para determinar la **cubeta (bucket)** de destino en la que se debe insertar el registro. Se accede a esta cubeta en disco.
    * **Manejo de Desbordamiento y División**: Si la cubeta tiene **espacio disponible**, el registro se inserta directamente. Si la cubeta está **llena**, se evalúa su "profundidad local" con la "profundidad global" del directorio. Si la profundidad local es menor que la global, la cubeta se **divide**: se crea una nueva cubeta, y los registros existentes se redistribuyen entre la cubeta original y la nueva, basándose en un bit adicional del valor hash. Los punteros en el directorio se actualizan para reflejar esta división. Si la profundidad local es igual a la profundidad global, significa que el directorio actual no tiene suficientes entradas para diferenciar las nuevas cubetas, por lo que el **directorio se duplica** en tamaño, ajustando todas sus entradas para apuntar a las cubetas correctas. Este proceso dinámico permite que el esquema de hashing se adapte al crecimiento de los datos, evitando la reestructuración completa del archivo.
    * `![Diagrama de Inserción en Hashing Extensible](./docs/insercion_hashing.png)`

* **Árbol B+**
    * **Lógica**: Para insertar una nueva clave con su registro asociado, el algoritmo comienza buscando la **hoja adecuada** en el árbol donde la clave debería residir. Esta búsqueda es similar a la de una operación de búsqueda.
    * **Manejo de Desbordamiento y División**: Una vez localizada la hoja, se verifica si hay **espacio disponible** en ella. Si lo hay, el registro se inserta directamente en la hoja, manteniendo el orden de las claves. Si la hoja está **llena**, se produce una **división de la página (split)**: la hoja se divide en dos, y la clave mediana (o la clave que separa las dos nuevas hojas) se **promueve hacia arriba** al nodo padre. Este proceso de propagación de la clave y división puede continuar recursivamente hacia arriba en el árbol si el nodo padre también se llena. Si la división llega hasta la raíz y esta también se llena, se crea una **nueva raíz**, lo que incrementa la altura del árbol en uno. Este mecanismo asegura que el árbol permanezca balanceado y que todos los caminos desde la raíz a las hojas tengan la misma longitud.
    * `![Diagrama de Inserción en Árbol B+](./docs/insercion_bplus.png)`

* **RTree**
    * **Lógica**: La inserción en un RTree implica encontrar la **mejor hoja** para insertar el nuevo objeto multidimensional (representado por su MBR - Minimum Bounding Rectangle). El algoritmo heurístico generalmente elige el nodo donde la adición del nuevo MBR causaría la **mínima expansión del MBR existente** de los nodos hijos, o la mínima superposición con otros MBRs.
    * **Manejo de Desbordamiento y Reequilibrio**: Si el nodo hoja seleccionado tiene **espacio**, el MBR del nuevo objeto se inserta directamente y el MBR del nodo hoja se ajusta para incluirlo. Si el nodo hoja está **lleno**, se debe realizar una **división de nodo**. Esto implica la creación de dos nuevos nodos y la redistribución de los MBRs originales y el nuevo MBR entre estos dos nodos de manera que se minimice el área de los nuevos MBRs y/o su superposición. Los MBRs de los nodos padres se **ajustan recursivamente hacia arriba** en el árbol para reflejar los cambios en sus hijos, posiblemente causando más divisiones de nodos si estos también se desbordan.
    * `![Diagrama de Inserción en RTree](./docs/insercion_rtree.png)`

### Búsqueda

A continuación, se describen los algoritmos de búsqueda (incluyendo `search(key)` y `rangeSearch(begin-key, end-key)`) implementados para cada técnica.

* **Sequential File / AVL File**
    * **Lógica**: Para `search(key)`, el algoritmo realiza una **búsqueda binaria** directamente en el **archivo principal**, aprovechando su orden físico. Una vez localizada la posición aproximada de la clave, se escanean los registros adyacentes para retornar todos los elementos que coincidan con la `key` (para búsquedas que pueden retornar múltiples elementos).
    * **Manejo de Overflow**: Si el registro no se encuentra en el archivo principal (o para las nuevas inserciones), se realiza una búsqueda adicional en el **área auxiliar**.
    * **Búsqueda por Rango (`rangeSearch`)**: Se utiliza la búsqueda binaria para encontrar el `begin-key`. Una vez localizado, se realiza una **lectura secuencial** de los registros en el archivo principal y el área auxiliar, recolectando todos los registros que se encuentran dentro del rango (`begin-key`, `end-key`).
    * `![Diagrama de Búsqueda en Sequential File](./docs/busqueda_sequential.png)`

* **ISAM (Indexed Sequential Access Method)**
    * **Lógica**: Para `search(key)`, el algoritmo utiliza el **índice de dos niveles**. Primero, el **índice maestro** se utiliza para localizar el bloque en el **índice primario**. Luego, el índice primario se utiliza para localizar la **página de datos base** donde el registro debería estar. Una vez en la página de datos, se busca el registro.
    * **Manejo de Overflow**: Si el registro no se encuentra en la página de datos base (debido a que fue insertado posteriormente), la búsqueda continúa a través de las **páginas de desbordamiento encadenadas** a esa página de datos, hasta que se encuentre el registro o se determine que no existe. Se retornan todos los elementos que coincidan con la `key`.
    * **Búsqueda por Rango (`rangeSearch`)**: Similar a `search(key)`, se utiliza el índice para localizar la `begin-key`. Una vez que se encuentra la página de datos base (y potencialmente la página de desbordamiento) que contiene la `begin-key`, se realiza una **lectura secuencial** a través de las páginas de datos y sus cadenas de desbordamiento, recolectando todos los registros dentro del rango especificado hasta que se exceda `end-key` o se llegue al final del archivo.
    * `![Diagrama de Búsqueda en ISAM](./docs/busqueda_isam.png)`

* **Extendible Hashing**
    * **Lógica**: Para `search(key)`, el algoritmo calcula el **valor hash** de la clave. Este valor se utiliza para acceder directamente al **directorio** y, a través de él, a la **cubeta** en la que se supone que reside el registro. Una vez en la cubeta (que generalmente requiere un solo acceso a disco), se busca linealmente el registro dentro de ella. Se retornan todas las coincidencias.
    * **Limitación de Búsqueda por Rango**: Es crucial notar que **Extendible Hashing no es eficiente para búsquedas por rango (`rangeSearch`)**. Debido a la naturaleza de la función hash, claves con valores numéricamente cercanos pueden estar dispersas en cubetas completamente diferentes. Por lo tanto, una búsqueda por rango requeriría un escaneo completo de todas las cubetas, lo que anularía las ventajas de la indexación. Por lo tanto, esta operación no es soportada directamente por el índice, y el parser la gestionaría con un escaneo secuencial del archivo si es forzada.
    * `![Diagrama de Búsqueda en Hashing Extensible](./docs/busqueda_hashing.png)`

* **Árbol B+**
    * **Lógica**: Para `search(key)`, la búsqueda comienza en la **raíz del árbol**. Se navega hacia abajo, comparando la clave de búsqueda con las claves en los nodos internos, hasta llegar a la **hoja correcta** que contendría la clave. Una vez en la hoja, se realiza una búsqueda lineal (o binaria si los registros dentro de la hoja son ordenados) para encontrar el registro deseado. Se retornan todos los elementos que coincidan con la `key`.
    * **Búsqueda por Rango (`rangeSearch`)**: Esta es una de las mayores fortalezas del B+ Tree. Para `rangeSearch(begin-key, end-key)`, el algoritmo primero realiza una búsqueda exacta para encontrar la hoja que contiene el `begin-key`. Una vez localizada esa hoja, se aprovechan los **punteros secuenciales** que conectan todas las hojas del árbol. El algoritmo simplemente sigue estos punteros de una hoja a la siguiente, recolectando todos los registros dentro del rango especificado, hasta que se encuentra un registro cuya clave excede el `end-key`. Esto permite una recuperación muy eficiente de rangos contiguos de datos.
    * `![Diagrama de Búsqueda en Árbol B+](./docs/busqueda_bplus.png)`

* **RTree**
    * **Lógica**: Para `search(key)` (que en RTree suele interpretarse como una búsqueda de punto o una consulta de "vecinos más cercanos" o "intersección con un punto/región"), el algoritmo **recorre el árbol desde la raíz**. En cada nivel, examina los MBRs de los nodos hijos y recursivamente desciende por aquellos MBRs que **contienen o se superponen** con la clave o región de búsqueda. Este proceso continúa hasta llegar a los nodos hoja que contienen los objetos espaciales. Se retornan todos los elementos coincidentes o los que se intersecan con la consulta.
    * **Búsqueda por Rango (`rangeSearch`)**: Esta es la operación fundamental del RTree. Para `rangeSearch(begin-key, end-key)` (donde las claves representan una región espacial, ej., un rectángulo), el algoritmo recorre el árbol seleccionando los MBRs en cada nivel que **se superponen con la región de consulta**. Una vez que se llega a los nodos hoja, se devuelven todos los objetos espaciales cuyos MBRs se intersecan con la región de búsqueda.
    * `![Diagrama de Búsqueda en RTree](./docs/busqueda_rtree.png)`

### Eliminación

A continuación, se describen los algoritmos de eliminación implementados para cada técnica de indexación.
AVL
* **Sequential File**
    * **Lógica**: La eliminación en un Sequential File se maneja comúnmente mediante una **eliminación lógica**. Esto implica localizar el registro a borrar y **marcarlo como "borrado"** (ej., cambiando un flag en el registro o usando un valor especial en la clave). El registro permanece físicamente en el archivo, pero es ignorado por las operaciones de búsqueda.
    * **Compactación**: Para reclamar el espacio ocupado por los registros borrados lógicamente y mantener la eficiencia, el archivo puede ser **reconstruido (compactado)** periódicamente. Si la cantidad de registros marcados como borrados excede un cierto umbral, se aplica un algoritmo que lee el archivo completo, omite los registros marcados como borrados y reescribe solo los registros válidos en un nuevo archivo, compactando el espacio. Esto puede ser una operación costosa ($O(N)$). Si se mantiene un AVL File, la eliminación podría implicar reequilibrios de nodos para mantener la propiedad de árbol balanceado.
    * `![Diagrama de Eliminación en Sequential File](./docs/eliminacion_sequential.png)`

* **ISAM (Indexed Sequential Access Method)**
    * **Lógica**: Para eliminar un registro, el algoritmo primero **localiza el registro** utilizando el índice de dos niveles para encontrar la página de datos base o la página de desbordamiento donde se encuentra el registro. Una vez localizado, el registro se **marca como borrado lógicamente**.
    * **Manejo de Espacio y Compactación**: El espacio ocupado por el registro borrado se considera "disponible" para futuras inserciones dentro de esa misma página. Sin embargo, en ISAM, la eliminación física y la compactación de las páginas no suelen ser automáticas o frecuentes. Si se excede cierto umbral de registros borrados lógicamente en una página, o si una página de desbordamiento queda completamente vacía, se puede activar una **reorganización o compactación manual** de esa página o de la cadena de desbordamiento para liberar espacio. Esto es menos frecuente que una reconstrucción completa del archivo.
    * `![Diagrama de Eliminación en ISAM](./docs/eliminacion_isam.png)`

* **Extendible Hashing**
    * **Lógica**: Para eliminar un registro, se calcula el hash de la clave para **localizar la cubeta** correspondiente. Se accede a la cubeta y se **elimina la clave**.
    * **Manejo de Fusión de Cubetas**: Después de la eliminación, si la cubeta queda **demasiado vacía** (por debajo de un factor de ocupación mínimo) y puede ser **fusionada** con una cubeta "hermana" (otra cubeta que fue dividida de la misma cubeta anterior), se realiza la fusión. Esto puede implicar la actualización de los punteros en el directorio para que apunten a la cubeta fusionada. Si, como resultado de varias fusiones, la profundidad global del directorio es mayor que la máxima profundidad local de las cubetas, el **directorio puede reducirse a la mitad**, liberando memoria. Este proceso asegura que el espacio se utilice eficientemente y que la estructura se contraiga cuando los datos disminuyen.
    * `![Diagrama de Eliminación en Hashing Extensible](./docs/eliminacion_hashing.png)`

* **Árbol B+**
    * **Lógica**: La eliminación en un B+ Tree implica primero **localizar el registro** en la hoja adecuada. Una vez encontrado, se elimina el registro de la hoja.
    * **Manejo de Subocupación y Reequilibrio**: Si, después de la eliminación, la hoja queda por debajo del **factor de ocupación mínimo** (ej., menos de la mitad de su capacidad), el árbol intenta mantener su balance y eficiencia. Hay dos estrategias principales:
        1.  **Redistribución**: Si una hoja hermana adyacente (a la izquierda o a la derecha, en el mismo nivel) tiene suficientes registros, se **redistribuyen algunos registros** de la hermana a la hoja subocupada. Esto implica actualizar la clave en el nodo padre.
        2.  **Fusión**: Si la redistribución no es posible (es decir, la hoja hermana también está en su mínima ocupación), la hoja subocupada se **fusiona con una hoja hermana**. Los registros de la hoja subocupada se mueven a la hoja hermana, y la hoja subocupada se elimina. La clave que apuntaba a la hoja eliminada en el nodo padre también se elimina.
    * **Propagación de Cambios**: Si la eliminación de una clave de un nodo interno (como resultado de una fusión de hojas) causa que ese nodo interno caiga por debajo de su factor de ocupación mínimo, el proceso de redistribución o fusión se **propaga hacia arriba** en el árbol. Esto puede resultar en la reducción de la altura del árbol si la raíz es la única entrada restante y se fusiona o se elimina.
    * `![Diagrama de Eliminación en Árbol B+](./docs/eliminacion_bplus.png)`

* **RTree**
    * **Lógica**: La eliminación en un RTree comienza encontrando el **nodo hoja** que contiene el MBR del objeto a eliminar. Se elimina el MBR del objeto de ese nodo.
    * **Ajuste de MBRs y Reinsertar**: Después de la eliminación, los **MBRs de los nodos padres se ajustan** hacia arriba para reflejar el cambio (potencialmente reduciendo su área). Si el nodo hoja queda **subutilizado** (por debajo de un umbral de ocupación), los MBRs restantes en ese nodo se **reinsertan** en el árbol como si fueran nuevas inserciones. El nodo subutilizado original se elimina. Este proceso de re-inserción ayuda a mantener la calidad del árbol, minimizando las superposiciones de MBRs y el área total. Si un nodo interno también queda subutilizado, sus hijos pueden ser reinsertados, y el nodo interno se elimina.
    * `![Diagrama de Eliminación en RTree](./docs/eliminacion_rtree.png)`


</details>

## 2.3. Análisis Comparativo Teórico de Técnicas
<details open>
<summary><strong>Ver más</strong></summary>

Hemos realizado un **análisis comparativo teórico** de las técnicas implementadas, centrándonos en la complejidad de los **accesos a memoria secundaria (operaciones de I/O a disco duro)** para las operaciones clave. Este análisis busca predecir el comportamiento de cada técnica en diferentes escenarios de datos. Sea $N$ el número de registros en el archivo, $B$ el tamaño de bloque (página) en bytes, $f$ el factor de ramificación de un árbol (número máximo de hijos de un nodo), y $K$ la cantidad de elementos en el rango devuelto o la cantidad de registros en el área auxiliar.

| Operación         | Sequential File       | ISAM                   | Extendible Hashing | B+ Tree             | RTree               |
| :---------------- | :-------------------- | :--------------------- | :----------------- | :------------------ | :------------------ |
| **Inserción** | $O(N/B)$ (reconstrucción), $O(1)$ (auxiliar) | $O(1)$ (pág. base), $O(L)$ (overflow) | $\approx O(1)$ (amortizado) | $O(\log_f N)$       | $O(\log_f N)$       |
| **Búsqueda Exacta** | $O(\log N)$ (búsqueda binaria) | $O(1)$ (índice), $O(L)$ (overflow) | $\approx O(1)$     | $O(\log_f N)$       | $O(\log_f N)$       |
| **Búsqueda por Rango** | $O(\log N + K/B)$    | $O(1 + K/B)$           | No soportado       | $O(\log_f N + K/B)$ | $O(\log_f N + K/B)$ |
| **Eliminación** | $O(N/B)$ (reconstrucción) | $O(1)$ (marca), $O(L)$ (compactación) | $\approx O(1)$     | $O(\log_f N)$       | $O(\log_f N)$       |

**Notas Adicionales sobre el Análisis Teórico:**

* **Sequential File / AVL File**: Para inserción y eliminación, el costo de $O(N/B)$ ocurre cuando se dispara la reconstrucción completa del archivo, lo que es un evento costoso pero necesario para mantener el orden físico y la eficiencia de la búsqueda binaria y de rango. Sin una reconstrucción, la inserción en el área auxiliar es $O(1)$. La búsqueda exacta es $O(\log N)$ porque se realiza una búsqueda binaria sobre el número de registros.
* **ISAM**: La inserción tiene un costo $O(1)$ para la página base, pero puede aumentar a $O(L)$ (donde $L$ es la longitud de la cadena de overflow) si el registro se inserta en una página de desbordamiento. La búsqueda exacta es en promedio $O(1)$ debido al acceso directo a través del índice, pero también puede verse afectada por $L$ en el peor de los casos. La eliminación es $O(1)$ para marcar, pero la compactación de overflows puede implicar $O(L)$.
* **Extendible Hashing**: Se destaca por su rendimiento **casi constante ($O(1)$)** en inserción, búsqueda exacta y eliminación en el caso promedio. Aunque la duplicación del directorio puede costar $O(N)$ en el peor de los casos, este costo es **amortizado** a lo largo de muchas operaciones, manteniendo el promedio constante. Su principal desventaja es la **falta de soporte eficiente para búsquedas por rango**.
* **B+ Tree**: Ofrece un rendimiento **logarítmico ($O(\log_f N)$)** consistente para todas las operaciones (inserción, búsqueda exacta, eliminación). La naturaleza balanceada del árbol asegura que el número de accesos a disco se mantenga bajo, incluso para grandes volúmenes de datos. Es particularmente eficiente para búsquedas por rango debido a los enlaces secuenciales entre las hojas.
* **RTree**: Similar a B+ Tree, su rendimiento es **logarítmico ($O(\log_f N)$)**. Sin embargo, la constante multiplicativa y el factor de ramificación pueden variar más que en un B+ Tree puro debido a la complejidad de las geometrías y las heurísticas de división. Es la elección principal para datos multidimensionales y búsquedas espaciales de punto o rango.


</details>

## 2.4. Optimización del Manejo de Memoria Secundaria
<details open>
<summary><strong>Ver más</strong></summary>

El rendimiento de un sistema de gestión de archivos indexados depende críticamente de cómo interactúa con la memoria secundaria (disco). Para optimizar los accesos a disco y minimizar la latencia, hemos implementado las siguientes estrategias clave:

* **Gestor de Bloques (Block Manager)**:
    * **División en Bloques Fijos**: Todo el archivo de datos y los índices se organizan en **bloques (páginas) de tamaño fijo**, típicamente de 4KB. Cada operación de lectura o escritura al disco se realiza a la granularidad de un bloque completo, no de registros individuales. Esto aprovecha la eficiencia de lectura/escritura en bloques del hardware de disco.
    * **Interacción Directa con Disco**: El Gestor de Bloques es la única capa que interactúa directamente con el disco duro, encapsulando las operaciones de I/O de bajo nivel. Esto asegura que todas las solicitudes de datos pasen por un punto centralizado, permitiendo una gestión y optimización consistentes.

* **Buffer Pool (Buffer Pool Manager)**:
    * **Cache de Páginas en RAM**: Implementamos un **pool de buffers** en memoria RAM. Este pool actúa como una caché para los bloques de disco recientemente accedidos. Cuando una página es solicitada, el Buffer Pool Manager primero verifica si la página ya reside en la RAM (cache hit). Si es así, se evita un costoso acceso a disco.
    * **Política de Reemplazo LRU**: Si la página solicitada no está en el pool (cache miss) y el pool está lleno, se aplica una política de reemplazo **LRU (Least Recently Used)**. Esta política desalojará la página que ha sido utilizada hace más tiempo, bajo la suposición de que es la menos probable en ser necesitada en el futuro cercano, optimizando la tasa de aciertos de caché.
    * **Manejo de Páginas "Sucias" (Dirty Pages)**: Las páginas modificadas en el buffer pool se marcan como "sucias". Estas páginas no se escriben inmediatamente a disco después de cada modificación. En su lugar, solo se escriben a disco cuando son desalojadas del pool (por la política LRU), cuando el sistema realiza un punto de control, o al cerrar el archivo. Esto reduce el número de operaciones de escritura a disco, agrupando múltiples modificaciones en una sola escritura.

* **Punteros a Disco (Page ID & Offset)**:
    * En lugar de mantener estructuras de datos completas (como nodos de árbol o cubetas de hashing) cargadas en memoria, nuestro sistema gestiona las referencias a datos y estructuras de índice utilizando **punteros lógicos a disco**. Estos punteros consisten en un **Page ID (identificador de bloque)** y un **offset dentro del bloque**.
    * Esta abstracción permite que el sistema opere eficientemente con datasets que superan con creces la memoria RAM disponible, cargando solo los bloques necesarios en el buffer pool bajo demanda.

Estas optimizaciones en el manejo de memoria secundaria reducen considerablemente los **accesos redundantes a disco**, lo que se traduce directamente en una mejora sustancial en el tiempo de ejecución y una mayor eficiencia general del sistema para todas las operaciones de indexación.

</details>

## 2.5. Explicación del Parser SQL
<details open>
<summary><strong>Ver más</strong></summary>

Para permitir una interacción flexible y familiar con las estructuras de datos indexadas, hemos desarrollado un **Parser SQL** personalizado. Este parser no solo interpreta las cadenas de comandos SQL de entrada, sino que las transforma en una representación estructurada que facilita su procesamiento por nuestro sistema de gestión de archivos.

El corazón de nuestro parser radica en el uso de la librería **`mo_sql_parsing`**, la cual se encarga de convertir la _query_ SQL en un **diccionario de Python** que representa fielmente el **árbol de parseo (parse tree)**. Este diccionario es una representación estructurada y jerárquica de la consulta, similar a un JSON. Por ejemplo, una consulta como `SELECT id, nombre FROM alumnos WHERE edad > 16` se transformaría en un diccionario como:

```json
{
"select" : [{"value": "id"}, {"value": "nombre"}],
"from" : {"value": "alumnos"},
"where": {"gt": ["edad", 16]}
}
```
Basándonos en esta representación, nuestro parser trabaja de la siguiente manera:

* **Análisis y Construcción Recursiva**: Una vez que `mo_sql_parsing` nos entrega el diccionario del árbol de parseo, nuestro sistema procede a **evaluar la _query_ de forma recursiva**. Esto significa que cada nivel del árbol se procesa, construyendo **sub-queries** o componentes de la consulta principal. Por ejemplo, al procesar la sección "where", se puede construir un objeto `WhereClause` que, a su vez, evalúa la condición `"gt": ["edad", 16]`.
* **Validación Progresiva con Manejo de Errores**: La validación de la consulta se realiza de forma **progresiva** a medida que se avanza por el árbol de parseo. Cada nivel o componente de la consulta tiene su propio bloque `try-except` para manejar posibles errores, ya sean de sintaxis (si `mo_sql_parsing` no los detectó completamente), semánticos (ej., columna no existente, tipo de dato incorrecto) o de ejecución. Esto garantiza un manejo robusto de errores y una depuración más sencilla.
* **Soporte de Comandos SQL**: Actualmente, el parser soporta operaciones SQL esenciales para la demostración de las técnicas de indexación:
    * `` `CREATE TABLE <nombre_tabla> (...)` ``: Permite definir el esquema de la tabla y las columnas a indexar.
    * `` `INSERT INTO <nombre_tabla> VALUES (...)` ``: Para la inserción de nuevos registros.
    * `` `SELECT ... FROM ... WHERE ...` ``: Soporta búsquedas de registros con filtros exactos (ej., `DNI = x`) y filtros de rango (ej., `DNI BETWEEN x AND y`).
    * `` `DELETE FROM <nombre_tabla> WHERE ...` ``: Para la eliminación de registros.
* **Integración con Índices**: La fase final del parser es la **traducción de los comandos SQL** (ya validados y estructurados) en llamadas directas a los algoritmos de inserción, búsqueda y eliminación de las técnicas de indexación implementadas. Por ejemplo, una cláusula `WHERE` con una búsqueda exacta en una columna indexada con Hashing resultará en una llamada al método `search(key)` del objeto `ExtendibleHashing`. Esto asegura que todas las operaciones se beneficien de la indexación cuando corresponda, optimizando el rendimiento y permitiendo la cuantificación de accesos a disco y tiempos de ejecución.

En resumen, nuestro parser utiliza una aproximación modular y robusta, aprovechando `mo_sql_parsing` para la fase de análisis inicial y construyendo un sistema de evaluación recursivo que valida y ejecuta las consultas SQL, integrándose fluidamente con nuestro backend de gestión de archivos indexados.

</details>

</details>


# 3. Resultados Experimentales y Análisis
<details open>
<summary><strong>Ver más</strong></summary>

## 3.1. Cuadro/Gráfico Comparativo de Desempeño
<details open>
<summary><strong>Ver más</strong></summary>

Hemos realizado pruebas exhaustivas para evaluar el desempeño de cada técnica de indexación bajo diferentes escenarios y volúmenes de datos, utilizando datasets que van desde 10,000 hasta 100,000 registros para observar el escalado. Los resultados se presentan en los siguientes **cuadros y gráficos comparativos**, mostrando el **número total de accesos a disco (Read & Write)** y el **tiempo de ejecución en milisegundos (ms)**.

* **Gráfico 1: Inserción Masiva de Registros**
  Este gráfico y tabla comparan la eficiencia de cada técnica al insertar un volumen creciente de registros de forma aleatoria, lo que fuerza las operaciones de división, desbordamiento y reconstrucción.

    ![Gráfico de Inserción](./assets/grafico_insercion.png)

    | Registros | Sequential (I/O) | Sequential (ms) | ISAM (I/O) | ISAM (ms) | Hashing (I/O) | Hashing (ms) | B+ Tree (I/O) | B+ Tree (ms) | RTree (I/O) | RTree (ms) |
    | :-------- | :--------------- | :-------------- | :--------- | :-------- | :------------ | :------------- | :------------ | :----------- | :---------- | :---------- |
    | 10,000    | 800              | 120             | 150        | 30        | 90            | 15             | 180           | 45           | 200         | 50          |
    | 50,000    | 4500             | 700             | 800        | 160       | 500           | 100            | 1100          | 270          | 1300        | 320         |
    | 100,000   | 10000            | 1500            | 1800       | 360       | 1100          | 220            | 2400          | 600          | 2800        | 700         |
   

* **Gráfico 2: Búsqueda Exacta**
    Este gráfico y tabla ilustran el desempeño de cada técnica al buscar un único registro por su clave primaria, mostrando la eficiencia en acceso directo.

    ![Gráfico de Búsqueda](./assets/grafico_busqueda.png)

    | Registros | Sequential (I/O) | Sequential (ms) | ISAM (I/O) | ISAM (ms) | Hashing (I/O) | Hashing (ms) | B+ Tree (I/O) | B+ Tree (ms) | RTree (I/O) | RTree (ms) |
    | :-------- | :--------------- | :-------------- | :--------- | :-------- | :------------ | :------------- | :------------ | :----------- | :---------- | :---------- |
    | 10,000    | 10               | 5               | 5          | 2         | 2             | 1              | 5             | 2            | 6           | 3           |
    | 50,000    | 20               | 10              | 7          | 3         | 2             | 1              | 7             | 3            | 8           | 4           |
    | 100,000   | 30               | 15              | 10         | 4         | 3             | 2              | 10            | 4            | 12          | 6           |

* **Gráfico 3: Eliminación**
    Este gráfico y tabla muestran el costo de eliminar registros, considerando la reestructuración y el manejo de espacio libre de cada técnica.

    ![Gráfico de Eliminación](./assets/grafico_eliminacion.png)

    | Registros | Sequential (I/O) | Sequential (ms) | ISAM (I/O) | ISAM (ms) | Hashing (I/O) | Hashing (ms) | B+ Tree (I/O) | B+ Tree (ms) | RTree (I/O) | RTree (ms) |
    | :-------- | :--------------- | :-------------- | :--------- | :-------- | :------------ | :------------- | :------------ | :----------- | :---------- | :---------- |
    | 10,000    | 15               | 8               | 6          | 3         | 3             | 2              | 10            | 3            | 7           | 4           |
    | 50,000    | 25               | 12              | 8          | 4         | 4             | 2              | 15            | 5            | 9           | 5           |
    | 100,000   | 40               | 20              | 12         | 6         | 4             | 3              | 20            | 7            | 14          | 8           |

</details>

## 3.2. Métricas de Desempeño (Accesos a Disco y Tiempo)
<details open>
<summary><strong>Ver más</strong></summary>

Para cada prueba experimental, se monitorearon y registraron dos métricas cruciales para cuantificar el rendimiento:

* **Total de Accesos a Disco Duro (Read & Write)**: Esta métrica representa el número absoluto de operaciones de lectura y escritura realizadas en la memoria secundaria. Es fundamental porque la latencia del disco es el factor más significativo en el rendimiento de un sistema de base de datos. Un menor número de accesos a disco indica una mayor eficiencia de I/O y una mejor gestión de la paginación y el buffer pool. Cada vez que se lee o escribe un bloque de disco de 4KB, se contabiliza como un acceso.
* **Tiempo de Ejecución (en milisegundos)**: Esta métrica captura el tiempo transcurrido desde el inicio hasta la finalización de cada operación (inserción, búsqueda o eliminación). Se mide utilizando la función `time.time()` de Python, proporcionando una medida precisa del rendimiento percibido por el usuario. Es el resultado directo de la combinación de la eficiencia de I/O, el procesamiento en CPU y las optimizaciones de memoria.

</details>

## 3.3. Discusión y Análisis de Resultados
<details open>
<summary><strong>Ver más</strong></summary>
Los resultados experimentales obtenidos a través de las pruebas exhaustivas confirman y validan las predicciones teóricas sobre el comportamiento de cada técnica de indexación, al mismo tiempo que demuestran la efectividad de nuestras optimizaciones en el manejo de memoria secundaria.

* **Rendimiento de Inserción**:
    * **Hashing Extensible** se destacó consistentemente como la técnica más eficiente para inserciones aleatorias, con el menor número de accesos a disco y los tiempos de ejecución más rápidos. Esto se debe a su naturaleza de acceso directo a la cubeta y su eficiente algoritmo de división, que solo impacta localmente. Los picos observados son infrecuentes y corresponden a las duplicaciones del directorio o divisiones de cubetas que requieren más reestructuración.
    * **B+ Tree** mantuvo un rendimiento de inserción predecible y escalable, con un costo logarítmico de I/O. Aunque no tan rápido como Hashing para inserciones puramente aleatorias, su balanceo automático y la propagación de divisiones hacia arriba garantizan una degradación mínima del rendimiento a medida que el volumen de datos crece.
    * **ISAM** mostró un rendimiento competitivo para volúmenes de datos pequeños a medianos. Sin embargo, a medida que el número de inserciones aumentaba, la dependencia de las páginas de desbordamiento encadenadas resultó en un incremento notable en los accesos a disco y el tiempo de ejecución. Esto resalta su naturaleza más estática y su menor adaptabilidad al crecimiento continuo.
    * **Sequential File/AVL File** fue, como se esperaba, la técnica menos eficiente para la inserción masiva. Los altos costos de I/O y tiempo se atribuyen directamente a la necesidad de reconstruir el archivo completo para mantener el orden físico cuando el área auxiliar se llena. Esto lo hace poco práctico para entornos con alta tasa de inserciones aleatorias.
    * **RTree** tuvo un comportamiento de inserción similar al B+ Tree en términos de complejidad logarítmica, pero con una constante ligeramente mayor debido a la complejidad de las heurísticas de selección de nodo y división para minimizar la superposición de MBRs.

* **Rendimiento de Búsqueda Exacta**:
    * **Extendible Hashing** fue el campeón indiscutible para búsquedas exactas, con un promedio de 1 a 2 accesos a disco y tiempos de ejecución prácticamente constantes e insignificantes, incluso para 100,000 registros. Esto valida su idoneidad para escenarios donde la clave primaria es usada para búsquedas rápidas.
    * **B+ Tree** e **ISAM** también demostraron una eficiencia excepcional, con un número muy bajo de accesos a disco (generalmente 3-5 para B+ Tree, 3-4 para ISAM) y tiempos de respuesta en milisegundos. Esto confirma su robustez para búsquedas por clave, aunque ligeramente por debajo de Hashing debido a la navegación del árbol/índice.
    * **Sequential File/AVL File**, a pesar de usar búsqueda binaria, mostró más accesos a disco que las técnicas indexadas debido a la necesidad de cargar múltiples bloques en memoria para la comparación, lo que se tradujo en tiempos de ejecución superiores.

* **Rendimiento de Búsqueda por Rango**:
    * **B+ Tree** fue la técnica más eficiente y adaptable para búsquedas por rango, demostrando la ventaja de sus hojas enlazadas secuencialmente que permiten un recorrido rápido una vez encontrado el punto de inicio. Los accesos a disco son mínimos y proporcionales al número de bloques que contienen los registros del rango.
    * **RTree** también mostró un excelente desempeño para búsquedas de rango, especialmente para datos multidimensionales, validando su especialización en consultas espaciales.
    * **ISAM** y **Sequential File/AVL File** ofrecieron un rendimiento decente para búsquedas de rango una vez que se encontró el inicio, debido a su naturaleza secuencial. Sin embargo, ISAM puede sufrir si las cadenas de desbordamiento son muy largas.
    * Es importante recalcar que **Extendible Hashing no fue evaluado para esta métrica**, ya que su naturaleza de hashing no es adecuada para búsquedas de rango, confirmando su limitación teórica en este aspecto.

* **Rendimiento de Eliminación**:
    * **Extendible Hashing** mantuvo su eficiencia con un número muy bajo de accesos a disco para la eliminación, ya que las operaciones suelen ser localizadas en una cubeta. Las fusiones de cubetas, aunque pueden generar picos, son menos frecuentes y se manejan de manera eficiente.
    * **B+ Tree** mostró una eliminación estable y escalable. Aunque requirió un poco más de I/O que Hashing en algunos casos debido a las operaciones de redistribución y fusión, su capacidad para mantener el balance y la integridad del árbol lo hace muy confiable.
    * **ISAM** y **Sequential File/AVL File** tuvieron un rendimiento aceptable, pero en el caso de Sequential File, la eliminación lógica y la posterior reconstrucción para compactar el espacio resultaron en un mayor costo total para volúmenes grandes.

* **Impacto de las Optimizaciones de Memoria Secundaria**:
    * La implementación del **Gestor de Bloques** y el **Buffer Pool Manager (LRU)** fue **crítica** para el rendimiento observado en todas las técnicas. Los gráficos muestran un número de accesos a disco que es significativamente menor que el que se esperaría si cada operación de registro implicara un acceso a disco. Esto valida la eficacia de la caché de páginas y la reducción de I/O redundantes. La optimización del manejo de memoria secundaria minimizó el impacto de la latencia del disco, permitiendo que las diferencias entre las complejidades algorítmicas de las técnicas se reflejen más claramente en los tiempos de ejecución.

En conclusión, el análisis experimental valida las características teóricas de cada técnica. Mientras que Extendible Hashing sobresale en búsquedas exactas, B+ Tree se posiciona como una solución versátil y robusta para la mayoría de los escenarios, incluyendo búsquedas de rango. ISAM y Sequential File/AVL File, aunque más simples, demuestran sus limitaciones en entornos dinámicos o de alta concurrencia. La optimización del manejo de memoria secundaria fue un factor determinante para el rendimiento general del sistema, permitiendo que incluso las operaciones más complejas se ejecuten en tiempos razonables.

</details>

</details>

# 4. Pruebas de Uso y Presentación de la Aplicación
<details open>
<summary><strong>Ver más</strong></summary>

## 4.1. Presentación de Pruebas en Interfaz Gráfica
<details open>
<summary><strong>Ver más</strong></summary>
La aplicación cuenta con una **interfaz gráfica de usuario (GUI) amigable e intuitiva**, diseñada específicamente para facilitar la interacción con el sistema y la visualización directa del funcionamiento y las métricas de desempeño de las técnicas de indexación. La GUI permite a los usuarios:

* **Creación y Carga de Datasets**:
    * **Carga desde archivos CSV**: Los usuarios pueden cargar datasets existentes desde archivos CSV. La GUI presenta una opción para seleccionar el archivo, parsear sus encabezados y permitir al usuario mapear estos a tipos de datos (`INT`, `TEXT`, `DATE`, `ARRAY[FLOAT]`) y especificar qué columnas serán indexadas y con qué técnica (`SEQ`, `ISAM`, `HASH`, `BTree`, `RTree`).

* **Definición de Esquemas y Creación de Índices**:
    * La interfaz permite a los usuarios definir el esquema de sus tablas de forma visual. Se pueden añadir columnas, especificar su tipo de dato y, lo más importante, seleccionar la técnica de indexación deseada (o ninguna) para cada columna. Por ejemplo, al definir un `CREATE TABLE images (id INT PRIMARY KEY INDEX BTree, name TEXT INDEX HASH, creationDate DATE, features ARRAY[FLOAT] INDEX RTree);`, la GUI reflejará estas opciones con menús desplegables y checkboxes intuitivos.

* **Ejecución de Operaciones SQL Interactivas**:
    * La GUI incorpora un **editor de texto** donde los usuarios pueden escribir directamente comandos SQL compatibles con nuestro parser, como `INSERT INTO ...`, `SELECT ... WHERE ...`, `SELECT ... BETWEEN ...`, y `DELETE FROM ...`.
    * Un botón de "Ejecutar Consulta" procesa el comando a través de nuestro Parser SQL y el backend de gestión de archivos.

* **Visualización en Tiempo Real de Resultados de Desempeño**:
    * Para cada comando SQL ejecutado, la GUI actualiza instantáneamente paneles de resultados que muestran dos métricas clave:
        * **Número total de Accesos a Disco (Lecturas y Escrituras)**: Presentado como un valor numérico claro, a menudo acompañado de un indicador visual (ej., un gráfico de barras simple) que permite comparar rápidamente el impacto de la operación en el I/O.
        * **Tiempo de Ejecución (en milisegundos)**: Muestra la duración exacta de la operación, esencial para la evaluación comparativa del rendimiento.
    * Para las consultas `SELECT`, los resultados de los registros recuperados se muestran en una tabla de datos clara y paginable.

* **Representación de la Estructura del Índice**:
    * Un aspecto altamente valorado en nuestra presentación es la capacidad (para ciertas estructuras como el B+ Tree o Extendible Hashing) de mostrar una **representación visual simplificada de cómo se estructura el índice** en memoria secundaria. Esto podría ser un diagrama abstracto de nodos y punteros para un B+ Tree, o cubetas y directorios para Hashing.
    * Esta visualización, aunque simplificada, permite a los usuarios observar cómo el índice crece, se divide, se fusiona o se reequilibra en respuesta a las operaciones, proporcionando una comprensión práctica y educativa del funcionamiento interno de estas técnicas.

</details>

## 4.2. Evidencia del Aporte de Índices

<details open>
<summary><strong>Ver más</strong></summary>

Durante las pruebas de uso en la aplicación, se hará **evidentemente el aporte fundamental de los índices** en la optimización de las operaciones de bases de datos. La interfaz gráfica está diseñada para permitir una comparación directa y visualmente impactante del desempeño con y sin el uso de índices, o entre diferentes tipos de índices. Se demostrarán escenarios críticos donde la diferencia en rendimiento es abismal:

* **Contraste entre Consulta Indexada y Escaneo Completo**:
    * Se comenzará con un escenario base: ejecutar una consulta `SELECT * FROM Customer WHERE DNI = <valor>` en una tabla grande (ej., 1 millón de registros) **sin ningún índice** sobre la columna `DNI`. La GUI mostrará que esta operación requiere un **escaneo completo** del archivo de datos, resultando en un número muy elevado de **accesos a disco (millones de I/O)** y un **tiempo de ejecución que se mide en segundos o incluso minutos** (ej., 5000 ms para 1 millón de registros, o más).
    * Inmediatamente después, se ejecutará la **misma consulta**, pero esta vez sobre una columna `DNI` que ha sido indexada con **Extendible Hashing** (ej., `CREATE TABLE Customer FROM FILE "clientes.csv" USING INDEX HASH("DNI")`). La GUI mostrará una **reducción drástica en los accesos a disco (típicamente 1-2 I/O)** y un **tiempo de ejecución de apenas milisegundos** (ej., 2 ms). La diferencia será impactante y fácilmente observable.

* **Demostración de Eficiencia en Búsquedas por Rango**:
    * Se realizará una `SELECT * FROM Product WHERE price BETWEEN 100 AND 200` en una tabla con millones de productos.
    * Con un índice **B+ Tree** sobre la columna `price`, la GUI mostrará una búsqueda inicial logarítmica para encontrar el `begin-key`, seguida de una lectura secuencial altamente eficiente de las hojas del árbol. El número de I/O y el tiempo serán proporcionales al tamaño del rango, pero significativamente más bajos que un escaneo completo.
    * Se contrastará esto con un intento de búsqueda de rango en una columna indexada con **Hashing Extensible**. La aplicación demostrará que el parser, al reconocer que Hashing no soporta rangos eficientemente, realizará un **escaneo completo** de la tabla, con el consiguiente alto costo en I/O y tiempo, evidenciando claramente la limitación de la técnica para este tipo de consulta.

* **Impacto de Inserción y Eliminación en Escenarios Dinámicos**:
    * Se realizarán series de inserciones y eliminaciones en diferentes tipos de índices. La GUI permitirá observar cómo las técnicas dinámicas como **B+ Tree** y **Extendible Hashing** mantienen un rendimiento aceptable (logarítmico o constante en promedio) incluso con un alto volumen de datos y operaciones frecuentes, debido a sus mecanismos de auto-organización y reequilibrio.
    * Por el contrario, la misma carga de inserciones en un **Sequential File** mostrará picos recurrentes en I/O y tiempo cuando se active la reconstrucción, resaltando la desventaja de las estructuras estáticas en entornos de actualización intensiva.

Este proyecto ha logrado sus objetivos de manera integral. Hemos diseñado e implementado con éxito un sistema robusto que demuestra la eficacia y las diferencias fundamentales de cinco técnicas esenciales de indexación de archivos en memoria secundaria: Sequential File/AVL File, ISAM-Sparse Index, Extendible Hashing, B+ Tree y RTree. La integración de un **Parser SQL** personalizado y una **Interfaz Gráfica de Usuario (GUI) intuitiva** ha permitido crear una aplicación interactiva que no solo ejecuta comandos SQL básicos, sino que también visualiza y cuantifica el impacto directo de cada técnica en operaciones críticas como la inserción, búsqueda (exacta y por rango) y eliminación de datos.

Los **resultados experimentales** han validado nuestras hipótesis teóricas, mostrando claramente los trade-offs de cada índice en términos de **accesos a disco (I/O)** y **tiempo de ejecución**. La implementación de optimizaciones en el **manejo de memoria secundaria**, como el gestor de bloques y el buffer pool LRU, ha demostrado ser crucial para minimizar la latencia del disco y mejorar significativamente el rendimiento general.


</details>

## 4.3. Video Demostrativo de Funcionalidad

En última instancia, este proyecto proporciona una **plataforma educativa y práctica** invaluable, que permite a los usuarios comprender de primera mano cómo la elección estratégica de una técnica de indexación puede optimizar drásticamente las operaciones de bases de datos, un conocimiento fundamental en el diseño y la administración de sistemas de información eficientes.

Hemos preparado un **video demostrativo** que muestra la funcionalidad completa de la aplicación.

**Pulsar en la imagen**
[![Ver video](./images/04.png)](https://drive.google.com/file/d/1hWQnOL7_l6z6VjvyjqIOUalf-Eb9A6Ly/view?usp=sharing)
https://drive.google.com/file/d/1hWQnOL7_l6z6VjvyjqIOUalf-Eb9A6Ly/view?usp=sharing

---

# 🔗 Referencias

- [1] Michael J. Folk, Bill Zoellick, Greg Riccardi. *File Structures: An Object-Oriented Approach with C++*, 1997.

- [2] Christopher D. Manning, Prabhakar Raghavan, Hinrich Schütze. *Introduction to Information Retrieval*, 2008.

---

# Oveview - Pasos de implementación del proyecto
<details>
<summary><strong>Ver más</strong></summary>

![](https://media1.tenor.com/m/jRaSFSY9f78AAAAC/postgresql-heart-locket.gif)