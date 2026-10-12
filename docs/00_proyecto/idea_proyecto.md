# Idea del proyecto

**Título:** Plataforma Inteligente para el Análisis, Segmentación y Predicción de Clientes en el e-commerce de ropa deportiva
**Empresa (ficticia):** SportSmart Perú — tienda online de ropa, calzado y accesorios deportivos
**Curso:** Minería de Datos — FISI, UNMSM
**Metodología:** CRISP-DM

---

## 1. Contexto

SportSmart Perú vende por web y app a clientes de 12 departamentos del país. Registra pedidos, pagos, envíos, campañas de marketing, navegación, atención al cliente, opiniones y devoluciones, pero usa esos datos solo para reportes descriptivos: no sabe qué clientes están por irse, qué productos se compran juntos ni cuánto venderá el próximo trimestre.

## 2. Problema

> La empresa toma decisiones comerciales (campañas, stock, descuentos) sin conocer a sus clientes a nivel individual, lo que genera pérdida de clientes, campañas poco efectivas y quiebres o excesos de inventario.

Evidencia del EDA (Presentación 1, `reports/eda.json`):

| Indicador | Valor |
|---|---|
| Clientes sin compra en los últimos 180 días | 71,0 % |
| Clientes con una sola compra | 24,8 % |
| Ventas concentradas en el 20 % de clientes | 65,5 % |
| Puntuación media con entrega a tiempo vs. con retraso | 4,08 vs. 2,75 |
| Tasa de apertura / CTR de campañas | 27,9 % / 9,7 % |

## 3. Propuesta de solución

Una plataforma que integra las 12 fuentes de datos y aplica técnicas de minería de datos para responder preguntas de negocio concretas, mostrando los resultados en un dashboard y exponiéndolos mediante una API.

## 4. Objetivos

**General:** Desarrollar una plataforma de minería de datos que permita analizar, segmentar y predecir el comportamiento de los clientes de SportSmart Perú para apoyar decisiones comerciales.

**Específicos:**

1. Integrar y depurar las 12 fuentes de datos del negocio (CRISP-DM: comprensión y preparación).
2. Segmentar a los clientes según su valor y comportamiento de compra.
3. Predecir el abandono de clientes y estimar su valor futuro.
4. Descubrir productos que se compran juntos para recomendaciones y paquetes.
5. Pronosticar las ventas mensuales por categoría.
6. Analizar las opiniones de los clientes para detectar causas de insatisfacción.
7. Desplegar los resultados en una API y un dashboard con explicabilidad y monitoreo.

## 5. Preguntas de negocio → técnica → carpeta

| # | Pregunta de negocio | Técnica | Datos principales | Carpeta |
|---|---|---|---|---|
| 1 | ¿Cómo están los datos y qué patrones generales hay? | EDA y calidad | Todas | `notebooks/01_eda` |
| 2 | ¿Cómo dejamos los datos listos para modelar? | Limpieza, integración, RFM | Todas | `notebooks/02_preparation` |
| 3 | ¿Qué productos se compran juntos? | Reglas de asociación (Apriori / FP-Growth) | detalle_pedido, productos | `notebooks/03_association` |
| 4 | ¿Qué tipos de clientes tenemos? | Clustering (K-Means, DBSCAN) sobre RFM | clientes, pedidos, navegación | `notebooks/04_clustering` |
| 5 | ¿Cuánto venderemos los próximos meses? | Series de tiempo (SARIMA / Prophet) | pedidos | `notebooks/05_timeseries` |
| 6 | ¿Qué clientes y productos están más conectados? | Grafos (cliente–producto, centralidad, comunidades) | pedidos, detalle_pedido | `notebooks/06_graphs` |
| 7 | ¿Cuánto gastará un cliente (CLV / ticket)? | Regresión | pedidos, clientes, navegación | `notebooks/07_regression` |
| 8 | ¿Qué clientes abandonarán? | Clasificación (churn) | todas las de comportamiento | `notebooks/08_classification` |
| 9 | ¿Qué opinan los clientes y por qué se quejan? | NLP (sentimiento, temas) | opiniones, atención | `notebooks/09_nlp` |

## 6. Alcance

**Incluye:** dataset sintético integrado (ene-2023 a sep-2026, 472 581 registros), modelos de las 7 técnicas, API de consulta, dashboard y documentación por fases CRISP-DM.

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
| 7 | Presentación 1 | Comprensión del negocio y de los datos | `docs/00_proyecto`, `notebooks/01_eda`, `src/data` |
| 10 | Presentación 2 | Preparación + primeros modelos | `notebooks/02–05`, `src/features` |
| 13 | Presentación 3 | Modelado y evaluación | `notebooks/06–09`, `src/models`, `src/evaluation` |
| 16 | Presentación 4 | Despliegue | `backend`, `frontend`, `deployment`, `src/monitoring` |

> Ajustar el contenido de las semanas 10–16 a lo que indique la guía del curso.
