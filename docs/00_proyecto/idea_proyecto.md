# Idea del proyecto

**Título:** Plataforma Inteligente para el Análisis, Segmentación y Predicción de Clientes en el e-commerce de ropa deportiva
**Empresa (ficticia):** SportSmart Perú — tienda online de ropa, calzado y accesorios deportivos
**Curso:** Minería de Datos — FISI, UNMSM
**Metodología:** CRISP-DM

---

## 1. Contexto

SportSmart Perú vende por web y app a clientes de 12 departamentos del país. Registra pedidos, pagos, envíos, campañas de marketing, navegación, atención al cliente, opiniones, devoluciones e inventario, pero usa esos datos solo para reportes descriptivos: no sabe qué clientes están por irse, qué productos se compran juntos ni cuánto venderá el próximo trimestre.

## 2. Problema

> La empresa toma decisiones comerciales (campañas, stock, descuentos) sin conocer a sus clientes a nivel individual, lo que genera pérdida de clientes, campañas poco efectivas y quiebres o excesos de inventario.

Evidencia del EDA (Presentación 1, `reports/eda.json`):

| Indicador | Valor |
|---|---|
| Clientes registrados sin ninguna compra válida (ene-2023 a sep-2026) | 48,0 % |
| Clientes registrados desde 2023 sin ninguna compra válida | 41,2 % |
| Compradores sin compra en los últimos 180 días | 71,0 % |
| Total de clientes sin compra en los últimos 180 días | 84,9 % |
| Compradores con una sola compra | 24,8 % |
| Ventas concentradas en el 20 % de compradores | 65,5 % |
| Puntuación media con entrega a tiempo vs. con retraso | 4,08 vs. 2,75 |
| Tasa de apertura / CTR de campañas | 27,9 % / 9,7 % |
| Pedidos asociados a una campaña | 17,0 % |
| Sesiones con carrito abandonado | 30,1 % |
| Índice estacional de ventas: diciembre vs. abril | 1,42 vs. 0,82 |
| Tickets de atención sobre stock | 12,6 % |
| Productos-mes con quiebre de stock: noviembre-diciembre vs. resto del año | 29,4 % vs. 7,7 % |
| Productos-mes con exceso de stock (más de 2 meses de venta media) | 8,9 % |

**Cómo se relaciona la evidencia con cada consecuencia del problema:**

| Consecuencia | Evidencia | Pregunta que busca resolverla |
|---|---|---|
| Pérdida de clientes | Inactividad a 180 días, compradores de una sola compra y clientes sin compra | ¿Qué clientes abandonarán? |
| Campañas poco efectivas | CTR de 9,7 % y solo 17,0 % de pedidos con campaña | ¿Qué segmentos existen y cuáles tienen mayor valor? |
| Quiebres o excesos de inventario | Quiebres de 29,4 % en noviembre-diciembre frente a 7,7 % el resto del año, y 8,9 % de productos-mes con exceso (tabla `inventario`) | ¿Cuál es la tendencia futura de las ventas? |
| Insatisfacción por el servicio | Puntuación de 4,08 con entrega a tiempo y 2,75 con retraso. Es una asociación, no prueba causalidad | ¿Qué opinan los clientes y qué temas aparecen? |

> **Bases de cálculo:** "clientes" son los 15 000 registrados y "compradores" los 7 802 con al menos un pedido válido (no cancelado, con monto y fecha dentro del periodo). La historia de pedidos empieza en ene-2023, así que un cliente registrado en 2021-2022 pudo haber comprado antes; por eso se muestra también la cifra de registrados desde 2023.

## 3. Propuesta de solución

Una plataforma que integra las 13 fuentes de datos y aplica técnicas de minería de datos para responder preguntas de negocio concretas, mostrando los resultados en un dashboard y exponiéndolos mediante una API.

## 4. Objetivos

**General:** Desarrollar una plataforma de minería de datos que permita analizar, segmentar y predecir el comportamiento de los clientes de SportSmart Perú para apoyar decisiones comerciales.

**Específicos:**

| # | Objetivo específico | Medida de logro (meta propuesta) | Entrega |
|---|---|---|---|
| 1 | Integrar, depurar y transformar las 13 fuentes de datos, aplicando ingeniería de características | Problemas de calidad del EDA tratados y documentados; dataset procesado disponible | Semana 10 |
| 2 | Descubrir productos que se compran juntos, comparando Apriori, FP-Growth y ECLAT | Reglas con lift > 1,5 y soporte ≥ 1 % | Semana 10 |
| 3 | Segmentar a los clientes según su valor y comportamiento (RFM, LRFM, CLV), con al menos dos algoritmos | Silhouette > 0,4 y segmentos interpretables | Semana 13 |
| 4 | Pronosticar las ventas a 7, 30, 60 y 90 días | MAPE < 15 % | Semana 13 |
| 5 | Analizar las relaciones entre clientes, productos y categorías mediante grafos | Nodos centrales identificados y comunidades con modularidad > 0,3 | Semana 13 |
| 6 | Estimar variables numéricas de negocio (ventas y valor del cliente) mediante regresión | R² > 0,6 | Semana 13 |
| 7 | Predecir el abandono de clientes mediante clasificación | AUC > 0,75 y recall de la clase "abandona" reportado | Semana 16 |
| 8 | Analizar las opiniones de los clientes para detectar temas y causas de insatisfacción | F1 de sentimiento > 0,75 | Semana 16 |
| 9 | Explicar las predicciones de los modelos con SHAP, LIME e importancia de variables | Explicación disponible por cliente en los modelos pertinentes | Semana 16 |
| 10 | Desplegar los resultados en una API y un dashboard, con monitoreo y mantenimiento | Aplicación funcional con control de data drift, versionado de modelos y auditoría | Semana 16 |

## 5. Preguntas de negocio → técnica → carpeta

| Tema | # | Pregunta de negocio | Técnica | Datos principales | Carpeta o módulo | Entrega |
|---|---|---|---|---|---|---|
| Clientes | 1 | ¿Qué segmentos de clientes existen? | Clustering (K-Means, DBSCAN) sobre RFM y LRFM | clientes, pedidos, navegacion | `notebooks/04_clustering` | Semana 13 |
| Clientes | 2 | ¿Qué clientes presentan mayor valor? | RFM, LRFM, CLV y ABC/XYZ | clientes, pedidos | `notebooks/04_clustering` | Semana 13 |
| Clientes | 3 | ¿Qué clientes presentan características similares? | Perfilado de clústeres | clientes, pedidos, navegacion | `notebooks/04_clustering` | Semana 13 |
| Ventas | 4 | ¿Cómo evolucionan las ventas? | EDA y descomposición temporal | pedidos | `notebooks/01_eda`, `notebooks/05_timeseries` | Semanas 7 y 13 |
| Ventas | 5 | ¿Cuál es la tendencia futura de las ventas? | Series de tiempo (SARIMA, Prophet) | pedidos, campanias, inventario | `notebooks/05_timeseries` | Semana 13 |
| Ventas | 6 | ¿Qué factores explican el comportamiento de las ventas? | Regresión e importancia de variables | pedidos, productos, campanias, navegacion | `notebooks/07_regression` | Semana 13 |
| Productos | 7 | ¿Qué productos se compran conjuntamente? | Apriori, FP-Growth y ECLAT | detalle_pedido, productos | `notebooks/03_association` | Semana 10 |
| Productos | 8 | ¿Qué productos tienen mayor asociación? | Soporte, confianza y lift | detalle_pedido, productos | `notebooks/03_association` | Semana 10 |
| Productos | 9 | ¿Qué productos presentan comportamientos similares? | Clustering de productos y ABC/XYZ | detalle_pedido, productos, devoluciones | `notebooks/04_clustering` | Semana 13 |
| Predicción | 10 | ¿Cuál será el volumen de ventas esperado? | Regresión | pedidos, productos, campanias, navegacion | `notebooks/07_regression` | Semana 13 |
| Predicción | 11 | ¿Cuánto gastará un cliente? | Regresión (CLV) | pedidos, clientes, navegacion | `notebooks/07_regression` | Semana 13 |
| Predicción | 12 | ¿Qué clientes tienen mayor probabilidad de abandonar? | Clasificación (churn) | todas las de comportamiento | `notebooks/08_classification` | Semana 16 |
| Predicción | 13 | ¿Qué variables influyen en cada predicción y por qué? | SHAP, LIME e importancia de variables | salidas de los modelos | `src/explainability` | Semana 16 |
| Relaciones | 14 | ¿Qué productos, clientes o categorías están fuertemente conectados? | Grafos y centralidad | pedidos, detalle_pedido, productos | `notebooks/06_graphs` | Semana 13 |
| Relaciones | 15 | ¿Qué comunidades o patrones pueden encontrarse? | Detección de comunidades | pedidos, detalle_pedido, productos | `notebooks/06_graphs` | Semana 13 |
| Textos | 16 | ¿Qué temas aparecen con mayor frecuencia en los comentarios? | NLP (modelado de temas) | opiniones, atencion | `notebooks/09_nlp` | Semana 16 |
| Textos | 17 | ¿Qué términos están relacionados? | Coocurrencia de términos y TF-IDF | opiniones | `notebooks/09_nlp` | Semana 16 |
| Textos | 18 | ¿Qué características tienen las opiniones de los clientes? | Análisis de sentimiento | opiniones | `notebooks/09_nlp` | Semana 16 |

El EDA (`notebooks/01_eda`) y la preparación (`notebooks/02_preparation`) no responden una pregunta de negocio propia: son etapas de apoyo para todas las anteriores.

## 6. Alcance

**Incluye:** dataset sintético integrado (ene-2023 a sep-2026, 487 056 registros), modelos de las 7 técnicas, API de consulta, dashboard y documentación por fases CRISP-DM.

**No incluye:** integración con sistemas reales de la empresa, pagos en línea ni despliegue productivo con usuarios reales.

## 7. Interesados (stakeholders)

| Área | Uso de la plataforma |
|---|---|
| Gerencia comercial | Pronóstico de ventas, concentración de ingresos |
| Marketing | Segmentos, clientes en riesgo, campañas dirigidas |
| Logística | Impacto de retrasos en satisfacción |
| Atención al cliente | Temas de quejas detectados por NLP |

## 8. Cronograma de entregas

| Semana | Entrega | Fases CRISP-DM | Carpetas involucradas |
|---|---|---|---|
| 7 | Presentación 1 | Comprensión del negocio y de los datos | `docs/00_proyecto`, `docs/01_metodologia`, `docs/02_datos`, `notebooks/01_eda`, `src/data` |
| 10 | Presentación 2 | Preparación, ingeniería de características, asociación y primer prototipo | `notebooks/02_preparation`, `notebooks/03_association`, `src/features` |
| 13 | Presentación 3 | Clustering, series de tiempo, grafos, regresión y evaluación comparativa | `notebooks/04_clustering`, `notebooks/05_timeseries`, `notebooks/06_graphs`, `notebooks/07_regression`, `src/models`, `src/evaluation` |
| 16 | Presentación 4 | Aplicación web, dashboard, clasificación, NLP, explicabilidad y monitoreo | `notebooks/08_classification`, `notebooks/09_nlp`, `src/explainability`, `src/monitoring`, `backend`, `frontend`, `deployment` |
