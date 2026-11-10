# Metodología CRISP-DM aplicada a SportSmart

## 1. Justificación

El proyecto sigue **CRISP-DM** (*Cross-Industry Standard Process for Data Mining*; Chapman et al., 2000), un proceso de seis fases independiente del sector y de la tecnología (Wirth & Hipp, 2000). Se comparó con las otras dos referencias habituales (Azevedo & Santos, 2008):

| Criterio del proyecto | CRISP-DM | KDD (Fayyad et al., 1996) | SEMMA (SAS) |
|---|---|---|---|
| Parte de un problema de negocio y define criterios de éxito | Fase propia | No es una etapa de su secuencia principal | No lo define como fase |
| Fases | Comprensión del negocio, comprensión de los datos, preparación, modelado, evaluación y despliegue | Selección, preprocesamiento, transformación, minería e interpretación | Muestreo, exploración, modificación, modelado y evaluación |
| Evalúa frente a objetivos de negocio | Sí | Interpreta los patrones encontrados | Evalúa principalmente el modelo |
| Incluye despliegue, monitoreo y mantenimiento | Sí | No como etapa de su secuencia principal | No lo define como fase |
| Dependencia de una herramienta | Ninguna | Ninguna | Asociado a productos SAS |

**Por qué se eligió para SportSmart:**

- **Nace del negocio:** el proyecto debe responder preguntas de negocio y medirse con KPIs, no solo entrenar modelos.
- **Cubre el producto final:** la propuesta exige aplicación web, monitoreo y mantenimiento, y CRISP-DM los contempla en el despliegue.
- **Coincide con las entregas:** sus fases se corresponden con las cuatro presentaciones del curso.
- **Es iterativo:** permite volver a fases anteriores, algo que ya ocurrió en este proyecto (sección 5).

## 2. Fases, entregas y estado

| Fase | Pregunta guía | Entrega | Estado |
|---|---|---|---|
| 1. Comprensión del negocio | ¿Qué problema resolvemos y cómo mediremos el éxito? | Semana 7 | ✅ Documentada |
| 2. Comprensión de los datos | ¿Qué datos hay y qué calidad tienen? | Semana 7 | ✅ Documentada |
| 3. Preparación de los datos | ¿Cómo limpiamos, integramos y transformamos? | Semanas 10 y 13 (presentación conjunta) | ✅ Documentada |
| 4. Modelado | ¿Qué técnica aplicamos a cada pregunta? | Semanas 10, 13 y 16 | 🟡 Parcial: faltan clasificación y minería de textos |
| 5. Evaluación | ¿Los modelos cumplen los criterios y sirven al negocio? | Semanas 13 y 16 | 🟡 Parcial: [evaluación comparativa](evaluacion_comparativa.md) hecha; falta explicabilidad |
| 6. Despliegue | ¿Cómo lo usa el negocio y cómo se mantiene? | Semana 16 | ⏳ Planificada |

## 3. Actividades por fase

### Fase 1. Comprensión del negocio ✅

| Actividad de CRISP-DM | Aplicación en SportSmart | Producto |
|---|---|---|
| Determinar los objetivos del negocio | Problema, consecuencias, evidencia, objetivos e interesados | [`idea_proyecto.md`](../00_proyecto/idea_proyecto.md) |
| Evaluar la situación | Alcance, riesgos y restricciones | [`idea_proyecto.md`](../00_proyecto/idea_proyecto.md), sección 6 de este documento |
| Determinar los objetivos de minería | 18 preguntas de negocio asociadas a técnicas y metas de los modelos | [`idea_proyecto.md`](../00_proyecto/idea_proyecto.md), sección 4 de este documento |
| Definir cómo medir el éxito del negocio | 16 KPIs con fórmula, línea base y meta | [`kpis.md`](../00_proyecto/kpis.md) |
| Elaborar el plan del proyecto | Cronograma alineado con las cuatro presentaciones | [`idea_proyecto.md`](../00_proyecto/idea_proyecto.md), sección 8 |

### Fase 2. Comprensión de los datos ✅

| Actividad de CRISP-DM | Aplicación en SportSmart | Producto |
|---|---|---|
| Recolectar los datos iniciales | Dataset simulado reproducible de 13 tablas y 487 056 registros | `data/raw/`, `src/data/generar_dataset.py` |
| Describir los datos | Diccionario de 92 campos y equivalencia con la propuesta | [`docs/02_datos/`](../02_datos/README.md), `diccionario_datos.xlsx` |
| Explorar los datos | EDA con 15 gráficos y 12 hallazgos | `notebooks/01_eda/01_eda_calidad.ipynb`, `reports/figures/` |
| Verificar la calidad | 23 problemas con impacto y tratamiento propuesto; 16 relaciones validadas | [`informe_calidad.md`](../02_datos/informe_calidad.md), `tests/test_datos.py` |

### Fase 3. Preparación de los datos ✅

| Actividad de CRISP-DM | Aplicación prevista | Producto |
|---|---|---|
| Seleccionar los datos | Definir tablas, periodo y variables por técnica | `notebooks/02_preparation` |
| Limpiar los datos | Aplicar los 23 tratamientos en el orden definido en el informe de calidad | `src/features`, `data/processed` |
| Construir datos | Variables RFM, LRFM, CLV, ABC/XYZ y comportamiento de compra | `src/features` |
| Integrar los datos | Vista por cliente, producto y periodo; relaciones para grafos | `data/processed` |
| Dar formato a los datos | One-Hot o Label Encoding, MinMaxScaler o StandardScaler, transacciones para asociación | `src/features` |
| Reducir y balancear | Eliminar colinealidad, seleccionar por importancia, PCA, LDA o QDA según corresponda; SMOTE, ADASYN, under u oversampling solo con datos de entrenamiento | `notebooks/02_preparation` |

### Fase 4. Modelado 🟡

Se ejecutan las cuatro actividades de CRISP-DM para cada técnica: seleccionar la técnica, diseñar la prueba, construir el modelo y evaluarlo técnicamente.

| Técnica | Algoritmos previstos | Diseño de la prueba | Entrega |
|---|---|---|---|
| Asociación | Apriori, FP-Growth y ECLAT | Comparar soporte, confianza, lift y resultados entre algoritmos | Semana 10 |
| Clustering | K-Means y DBSCAN, sobre RFM y LRFM | Silhouette e interpretación de segmentos | Semana 13 |
| Series de tiempo | SARIMA y Prophet, con LSTM como opción | Reserva temporal de los últimos 6 meses; pronósticos a 7, 30, 60 y 90 días | Semana 13 |
| Grafos | NetworkX: centralidad y comunidades | Modularidad e interpretación de comunidades | Semana 13 |
| Regresión | Lineal, Ridge, Lasso, Random Forest y XGBoost | Partición temporal; RMSE y R² | Semana 13 |
| Clasificación | Random Forest, XGBoost, SVM y Naive Bayes | Abandono = 180 días sin compra; variables calculadas antes del corte y etiqueta observada después | Semana 16 |
| Minería de textos | Pipeline de la propuesta, TF-IDF y sentimiento | Partición entrenamiento-prueba sin repetir textos idénticos entre ambas | Semana 16 |

### Fase 5. Evaluación 🟡

| Actividad de CRISP-DM | Aplicación prevista | Producto |
|---|---|---|
| Evaluar los resultados | Contrastar modelos con los criterios de la sección 4 y su aporte a los KPIs; comparación entre modelos | `src/evaluation`, `reports/` |
| Explicar las predicciones | SHAP, LIME, importancia de variables y visualización de decisiones | `src/explainability` |
| Revisar el proceso | Comprobar fugas de información, supuestos y decisiones de preparación | `reports/` |
| Determinar los siguientes pasos | Decidir qué modelos se despliegan, cuáles se ajustan y cuáles se descartan | Presentaciones de las semanas 13 y 16 |

### Fase 6. Despliegue ⏳

| Actividad de CRISP-DM | Aplicación prevista | Producto |
|---|---|---|
| Planificar el despliegue | API con FastAPI, base de datos y dashboard web con Docker | `backend`, `frontend`, `deployment` |
| Planificar monitoreo y mantenimiento | Rendimiento, data drift, reentrenamiento, versionado de modelos, logging y auditoría | `src/monitoring` |
| Elaborar el informe final | Documentación técnica y sustentación | `docs/` |
| Revisar el proyecto | Lecciones aprendidas | Presentación de la semana 16 |

## 4. Criterios de éxito

Estos criterios evalúan a los modelos. El éxito para el negocio se mide con los [KPIs](../00_proyecto/kpis.md).

| Técnica | Métrica | Meta orientativa |
|---|---|---|
| Asociación | Lift de las reglas seleccionadas, por subcategoría | > 1,5 con soporte ≥ 1 % |
| Clustering | Silhouette, con 3 segmentos | > 0,4 y segmentos interpretables |
| Series de tiempo | MAPE semanal sobre los últimos 6 meses; se reportan también el MAPE diario y el error acumulado a 7, 30, 60 y 90 días | < 15 % |
| Grafos | Modularidad de las comunidades | > 0,3 |
| Regresión | RMSE / R² de ventas por producto y mes; el valor del cliente se reporta como análisis secundario | R² > 0,6 |
| Clasificación (churn) | Recall de la clase "abandona", AUC | AUC > 0,75 |
| NLP | F1 de sentimiento | > 0,75 |

> Las metas son una propuesta inicial del equipo; se validan con el docente. Antes del modelado se ajustó el nivel de medición de asociación, series y regresión tras pruebas de viabilidad: por producto casi no hay pares con soporte suficiente, las ventas diarias son muy variables y 73,5 % de los compradores no gasta en los 12 meses siguientes. Los valores de las metas no cambiaron, y los resultados que no las alcancen se reportarán tal cual.

## 5. Iteraciones realizadas

CRISP-DM admite volver a fases anteriores. Durante la semana 7 ya ocurrió:

| Se detectó en | Hallazgo | Se volvió a | Resultado |
|---|---|---|---|
| Comprensión de los datos | El problema mencionaba quiebres de inventario, pero no había datos que lo sustentaran | Recolección de datos y problema | Se agregó la tabla `inventario` y el problema ahora se apoya en evidencia directa |
| Exploración de los datos | El 71 % de inactividad se calculaba solo sobre compradores; 48,0 % de los clientes no tenía compra válida | Comprensión del negocio | Se corrigió la evidencia y se agregó un KPI de activación |
| Verificación de los datos | Los pedidos del 30 de setiembre quedaban fuera del análisis | Exploración de los datos | Se corrigió el filtro y se recalcularon las cifras |
| Exploración de los datos | 97,6 % de las recompras ocurre en 180 días o menos | Objetivos de minería | Se sustentó la definición de abandono |
| Pruebas de viabilidad del modelado | Las metas de asociación, series y regresión no eran alcanzables al nivel planteado | Objetivos de minería | Se ajustó el nivel de medición sin cambiar los valores de las metas |

## 6. Riesgos y restricciones

| Riesgo o restricción | Efecto | Respuesta |
|---|---|---|
| Los datos son simulados | Los patrones reflejan el generador y las metas no pueden comprobarse en operación | Declararlo en cada entrega; evaluar el método y no el impacto real |
| Comentarios poco variados (3,7 % únicos) | Las métricas de NLP pueden salir optimistas | Separar textos idénticos entre entrenamiento y prueba |
| Navegación parcial (23,0 % de clientes, desde ene-2025) | Variables no disponibles para todos | Indicador de disponibilidad o modelos con y sin navegación |
| Fuga de información en churn y series | Métricas engañosamente altas | Particiones temporales; ajustar imputación y balanceo solo con entrenamiento |
| Variables redundantes (frecuencia y gasto: 0,93) | Inestabilidad y explicaciones confusas | Eliminar colinealidad en la preparación |
| Metas propuestas por el equipo | Podrían no ser las esperadas | Validarlas con el docente |

## Referencias

Azevedo, A., & Santos, M. F. (2008). KDD, SEMMA and CRISP-DM: A parallel overview. En *Proceedings of the IADIS European Conference on Data Mining 2008* (pp. 182-185). IADIS.

Chapman, P., Clinton, J., Kerber, R., Khabaza, T., Reinartz, T., Shearer, C., & Wirth, R. (2000). *CRISP-DM 1.0: Step-by-step data mining guide*. SPSS Inc.

Fayyad, U., Piatetsky-Shapiro, G., & Smyth, P. (1996). From data mining to knowledge discovery in databases. *AI Magazine, 17*(3), 37-54. https://doi.org/10.1609/aimag.v17i3.1230

Wirth, R., & Hipp, J. (2000). CRISP-DM: Towards a standard process model for data mining. En *Proceedings of the 4th International Conference on the Practical Applications of Knowledge Discovery and Data Mining* (pp. 29-39).
