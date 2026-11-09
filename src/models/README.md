# src/models

Entrenamiento y guardado de modelos. Los modelos entrenados van en `src/models/artifacts/` (ignorado por git).

| Módulo | Qué hace | Salida |
|---|---|---|
| `asociacion.py` | Compara Apriori, FP-Growth y ECLAT; genera y valida reglas por subcategoría. Ejecutar: `python -m src.models.asociacion` | `reports/asociacion.json`, `reports/reglas_asociacion.csv` |
| `clustering.py` | Compara K-Means, jerárquico y DBSCAN; perfila segmentos y agrupa productos. Ejecutar: `python -m src.models.clustering` | `reports/clustering.json`, `data/processed/segmentos_clientes.csv` |
