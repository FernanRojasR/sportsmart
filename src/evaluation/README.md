# src/evaluation

Métricas y comparación de modelos (matriz de confusión, AUC, silhouette, MAPE, RMSE).

| Módulo | Qué hace | Salida |
|---|---|---|
| `comparacion.py` | Consolida las técnicas frente a metas y referencias simples, con intervalos de confianza. Ejecutar: `python -m src.evaluation.comparacion` | `reports/evaluacion.json`, `docs/01_metodologia/evaluacion_comparativa.md` |
| `graficos.py` | Gráficos de la evaluación comparativa y de la regresión. Ejecutar: `python -m src.evaluation.graficos` | `reports/figures/evaluacion_comparativa.png`, `regresion_validacion_prueba.png`, `regresion_factores_detalle.png` |
