# src/features

Funciones de limpieza y construcción de variables (RFM, recencia, frecuencia, ticket, días desde última compra, etc.) reutilizadas por los notebooks y la API.

| Módulo | Qué hace | Salida |
|---|---|---|
| `preparacion.py` | Aplica los tratamientos del informe de calidad e integra las tablas. Ejecutar: `python -m src.features.preparacion` | `data/processed/*.csv`, `reports/preparacion.json` |
