# src/features

Funciones de limpieza y construcción de variables (RFM, recencia, frecuencia, ticket, días desde última compra, etc.) reutilizadas por los notebooks y la API.

| Módulo | Qué hace | Salida |
|---|---|---|
| `preparacion.py` | Aplica los tratamientos del informe de calidad e integra las tablas. Ejecutar: `python -m src.features.preparacion` | `data/processed/*.csv`, `reports/preparacion.json` |
| `variables.py` | Construye RFM, LRFM, CLV, ABC/XYZ, abandono, serie diaria y panel producto-mes, con fecha de corte para evitar fuga de información | `data/processed/*.csv` |
| `seleccion.py` | Colinealidad, selección por importancia, PCA/LDA/QDA, codificación, escalamiento y balanceo | `reports/caracteristicas.json` |
