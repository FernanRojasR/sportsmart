# src/models

Entrenamiento y guardado de modelos. Los modelos entrenados van en `src/models/artifacts/` (ignorado por git).

| Módulo | Qué hace | Salida |
|---|---|---|
| `asociacion.py` | Compara Apriori, FP-Growth y ECLAT; genera y valida reglas por subcategoría. Ejecutar: `python -m src.models.asociacion` | `reports/asociacion.json`, `reports/reglas_asociacion.csv` |
| `clustering.py` | Compara K-Means, jerárquico y DBSCAN; perfila segmentos y agrupa productos. Ejecutar: `python -m src.models.clustering` | `reports/clustering.json`, `data/processed/segmentos_clientes.csv` |
| `series.py` | Compara referencia estacional, SARIMA, SARIMAX y Prophet; pronostica a 7, 30, 60 y 90 días. Ejecutar: `python -m src.models.series` | `reports/series.json`, `reports/pronostico_ventas.csv` |
| `grafos.py` | Grafo cliente-producto y proyección producto-producto: comunidades, centralidad y patrones. Ejecutar: `python -m src.models.grafos` | `reports/grafos.json`, `reports/grafo_productos.csv` |
| `regresion.py` | Compara modelos de regresión de ventas por producto y mes; analiza el valor futuro del cliente. Ejecutar: `python -m src.models.regresion` | `reports/regresion.json`, `reports/predicciones_regresion.csv` |
