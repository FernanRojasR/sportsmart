# Informe de calidad de datos — SportSmart Perú

Fase CRISP-DM: **Comprensión de los datos**. Este informe diagnostica los datos crudos y propone su tratamiento; la limpieza se aplicará en la fase de preparación (semana 10), sin modificar `data/raw`.

Las cifras provienen de `src/data/eda_calidad.py` y están en `reports/eda.json` (secciones `calidad` y `calidad_diagnostico`).

## 1. Resumen

| Indicador | Resultado |
|---|---|
| Registros evaluados | 487 056 en 13 tablas |
| Incidencias de calidad | 5 031 (1,03 % de los registros) |
| Tabla con más incidencias | `clientes`: 2 744, el 54,5 % del total |
| Relaciones entre tablas sin registros huérfanos | 16 de 16 |
| Ventas excluidas del EDA por montos nulos o fechas inválidas | S/ 19 885,95 (0,14 %) |

**Conclusión:** la calidad es buena para iniciar la preparación. Los errores son puntuales y la estructura entre tablas es consistente, pero sin tratarlos se distorsionarían las series de tiempo y las segmentaciones. La mayoría de los valores dañados se puede reconstruir con otras columnas.

> El dataset es simulado y estos errores se introdujeron a propósito para esta fase.

## 2. Criterios

**Dimensiones evaluadas:** completitud (faltantes), unicidad (duplicados), validez (valores fuera de regla) y consistencia (formatos o cálculos que no coinciden).

**Severidad:**

- **Alta:** invalida un análisis o crea valor inexistente.
- **Media:** sesga resultados de alguna técnica.
- **Baja:** efecto marginal por su volumen.

## 3. Problemas detectados y tratamiento propuesto

El porcentaje se calcula sobre las filas de cada tabla.

| ID | Tabla · campo | Dimensión | Casos | % | Severidad | Impacto si no se trata | Tratamiento propuesto |
|---|---|---|---|---|---|---|---|
| Q01 | `pedidos.fecha_pedido` (fecha 2030-01-01) | Validez | 25 | 0,04 | Alta | Extiende la serie hasta 2030 y genera recencias negativas | Reconstruir como `fecha_envio` − 1 día. **Recuperables: 25 de 25** (se pierde la hora) |
| Q02 | `clientes.departamento` mal escrito | Consistencia | 752 | 5,00 | Alta | Fragmenta los departamentos y distorsiona ventas por zona | Normalizar mayúsculas y variantes (Cuzco → Cusco). **Recuperables: 752 de 752** |
| Q03 | `clientes.genero` no estándar | Consistencia | 580 | 3,86 | Alta | 7 valores para 2 categorías; crea columnas falsas al codificar | Unificar a M/F. **Recuperables: 580 de 580** |
| Q04 | `clientes` filas duplicadas | Unicidad | 45 | 0,30 | Alta | Infla la base y multiplica pedidos al unir tablas | Eliminar por `cliente_id`: las 45 repeticiones son filas idénticas |
| Q05 | `detalle_pedido` filas duplicadas | Unicidad | 120 | 0,12 | Alta | Crea S/ 13 497,34 inexistentes y altera canastas | Eliminar duplicados exactos |
| Q06 | `pedidos.monto_total` nulo | Completitud | 60 | 0,09 | Media | Excluye S/ 14 136,77 de las ventas | Reconstruir sumando `importe` del detalle. **Recuperables: 60 de 60** |
| Q07 | `detalle_pedido.cantidad` ≤ 0 | Validez | 20 | 0,02 | Media | Unidades negativas o nulas sesgan inventario y canastas | Recalcular con `importe ÷ (precio_unitario × (1 − descuento))` |
| Q08 | `detalle_pedido.cantidad` > 10 (hasta 99) | Validez | 20 | 0,02 | Media | Picos falsos de unidades | Igual que Q07. **Q07 y Q08 recuperables: 40 de 40** |
| Q09 | `pagos.importe` no cuadra con el pedido | Consistencia | 80 | 0,13 | Media | Exceso de S/ 10 855,81 en lo cobrado | Usar `pedidos.monto_total` y marcar el caso para auditoría |
| Q10 | `clientes.edad` nula | Completitud | 901 | 5,99 | Media | Reduce filas para modelar | Imputar con la mediana y agregar indicador `edad_faltante` |
| Q11 | `clientes.edad` fuera de 16-90 | Validez | 14 | 0,09 | Media | Valores imposibles (−1, 199) alteran medias y escalas | Convertir a nulo y tratar como Q10 |
| Q12 | `logistica.dias_entrega` > 40 | Validez | 20 | 0,03 | Media | Eleva promedios de entrega | Convertir a nulo e imputar con la mediana de su zona; conservar `entrega_a_tiempo` |
| Q13 | `opiniones.puntuacion` fuera de 1-5 | Validez | 15 | 0,07 | Media | Altera promedios y etiquetas de sentimiento | Convertir a nulo y excluir del entrenamiento de sentimiento |
| Q14 | `inventario` recepciones nulas o atípicas | Completitud, validez | 49 | 0,34 | Media | Rompe el balance y distorsiona quiebres y excesos | Reconstruir con la fórmula de balance. **Recuperables: 48 de 49** |
| Q15 | `inventario.stock_final` negativo | Validez | 20 | 0,14 | Media | Stock imposible | Reconstruir con la fórmula de balance. **Recuperables: 19 de 20** |
| Q16 | `inventario` filas duplicadas | Unicidad | 30 | 0,21 | Media | Cuenta dos veces un mismo producto-mes | Eliminar duplicados exactos |
| Q17 | `productos.precio_lista` nulo | Completitud | 5 | 1,56 | Media | Impide calcular margen y variables de precio | Tomar `precio_unitario` del detalle. **Recuperables: 5 de 5** |
| Q18 | `opiniones.comentario` vacío | Completitud | 1 145 | 5,00 | Baja | Sin texto para NLP | Excluir solo de NLP; conservar la puntuación |
| Q19 | `clientes.genero` nulo | Completitud | 452 | 3,00 | Baja | Reduce filas para modelar | Categoría "No declarado" |
| Q20 | `pagos.metodo` nulo | Completitud | 634 | 1,00 | Baja | Subestima levemente cada método | Categoría "No registrado" |
| Q21 | `logistica.distancia_km` negativa | Validez | 30 | 0,05 | Baja | Distancias imposibles | Usar el valor absoluto |
| Q22 | `atencion.horas_resolucion` negativa | Validez | 12 | 0,21 | Baja | Tiempos imposibles | Usar el valor absoluto |
| Q23 | `productos.marca` nula | Completitud | 3 | 0,93 | Baja | Sin marca para 3 productos | Categoría "Sin marca" |

En Q14 y Q15 hay un caso sin recuperar cada uno: se tratarán como faltantes. En `inventario`, los 29 registros con balance incorrecto se explican por las recepciones atípicas y los stocks negativos.

## 4. Nulos estructurales (no son errores)

| Campo | Casos | Significado | Tratamiento |
|---|---|---|---|
| `pedidos.campania_id` | 52 639 | Compra sin campaña | Conservar; crear indicador `con_campania` |
| `detalle_pedido.talla` | 48 678 | Producto sin talla | Conservar |
| `devoluciones.talla` | 1 140 | Producto sin talla | Conservar |
| `logistica.dias_entrega` y `entrega_a_tiempo` | 3 121 cada uno | Pedido cancelado o en tránsito | Conservar; excluir de métricas de entrega |

## 5. Controles sin problemas o ya explicados

| Control | Resultado |
|---|---|
| Integridad referencial (16 relaciones) | 0 registros huérfanos |
| Pedidos anteriores al registro del cliente | 0 |
| Clics sin apertura del mensaje | 0 |
| `monto_total` frente a la suma del detalle | 0 diferencias |
| Pagos por pedido | Máximo 1 |
| Envíos anteriores al pedido | 25, todos causados por Q01 |
| Opiniones anteriores al pedido | 10, todas causadas por Q01 |

Estos controles se repiten en `tests/test_datos.py` para las 16 relaciones.

## 6. Valores atípicos legítimos

Se evaluaron con IQR (1,5) y Z-score (|z| > 3) sobre valores ya válidos. Representan colas naturales de la distribución, no errores, por lo que **no se eliminan**.

| Variable | Atípicos IQR | % IQR | Atípicos Z-score | Máximo |
|---|---|---|---|---|
| `pedidos.monto_total` | 1 138 | 1,89 | 406 | S/ 1 028,30 |
| `productos.precio_lista` | 18 | 5,70 | 6 | S/ 532,90 |
| `logistica.dias_entrega` | 1 339 | 2,22 | 487 | 13 días |
| `logistica.distancia_km` | 606 | 0,96 | 681 | 2 403,3 km |
| `atencion.horas_resolucion` | 401 | 7,04 | 89 | 451,4 h |
| `navegacion.sesiones` | 1 696 | 5,17 | 647 | 35 sesiones |

**Tratamiento propuesto:** conservarlos y, según el modelo, aplicar transformación logarítmica o escalamiento robusto. En clustering se evaluará su efecto antes de decidir si se limitan.

## 7. Orden de aplicación en la preparación

El orden importa porque algunos tratamientos dependen de otros:

1. Eliminar duplicados (Q04, Q05, Q16), para no sumar importes repetidos.
2. Corregir cantidades (Q07, Q08) y reconstruir montos (Q06), luego importes de pago (Q09).
3. Reconstruir fechas (Q01) y filtrar el periodo hasta 2026-09-30.
4. Normalizar categorías (Q02, Q03) y completar categorías faltantes (Q19, Q20, Q23).
5. Corregir valores inválidos (Q11 a Q13, Q15, Q21, Q22), reconstruir inventario y precios (Q14, Q17).
6. Imputar edad y entrega (Q10, Q12), una vez corregidos los valores inválidos. En los modelos, ajustar la imputación solo con datos de entrenamiento.
7. Volver a ejecutar estos controles sobre `data/processed` y registrar el antes y el después.

## 8. Efecto esperado en los resultados

El EDA actual excluye los registros inválidos. Tras aplicar el tratamiento, las ventas subirán en S/ 19 885,95 (+0,14 %) al recuperar pedidos con monto nulo o fecha inválida, por lo que las cifras del EDA y las líneas base de KPIs podrían variar levemente.

## 9. Limitaciones

- **Errores conocidos:** al ser simulados, varias reconstrucciones son exactas; en datos reales habría que validarlas con el área responsable.
- **Fechas reconstruidas:** Q01 recupera el día, pero no la hora.
- **Aplicación del tratamiento:** los tratamientos están implementados en `src/features/preparacion.py`; el resultado de los controles antes y después está en `reports/preparacion.json` y en `notebooks/02_preparation/02_preparacion.ipynb`.
