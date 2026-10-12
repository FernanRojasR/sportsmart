# Metodología CRISP-DM aplicada a SportSmart

| Fase | Pregunta guía | Dónde queda en el repo | Estado |
|---|---|---|---|
| 1. Comprensión del negocio | ¿Qué problema resolvemos y cómo mediremos el éxito? | `docs/00_proyecto/idea_proyecto.md` | ✅ Presentación 1 |
| 2. Comprensión de los datos | ¿Qué datos hay y qué calidad tienen? | `notebooks/01_eda`, `src/data/eda_calidad.py`, `reports/eda.json`, `docs/02_datos` | ✅ Presentación 1 |
| 3. Preparación de los datos | ¿Cómo limpiamos, integramos y transformamos? | `notebooks/02_preparation`, `src/features`, `data/processed` | ⏳ |
| 4. Modelado | ¿Qué técnicas aplicamos a cada pregunta? | `notebooks/03–09`, `src/models` | ⏳ |
| 5. Evaluación | ¿Los modelos cumplen los criterios de éxito? | `src/evaluation`, `src/explainability`, `reports/` | ⏳ |
| 6. Despliegue | ¿Cómo lo usa el negocio? | `backend`, `frontend`, `deployment`, `src/monitoring` | ⏳ |

## Criterios de éxito (propuestos)

| Técnica | Métrica | Meta orientativa |
|---|---|---|
| Asociación | Lift de las reglas seleccionadas | > 1,5 con soporte ≥ 1 % |
| Clustering | Silhouette | > 0,4 y segmentos interpretables |
| Series de tiempo | MAPE en los últimos 6 meses | < 15 % |
| Regresión | RMSE / R² | R² > 0,6 |
| Clasificación (churn) | Recall de la clase "abandona", AUC | AUC > 0,75 |
| NLP | F1 de sentimiento | > 0,75 |

> Las metas son una propuesta inicial del equipo; se validan con el docente.
