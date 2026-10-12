# data

| Carpeta | Contenido | ¿Se versiona? |
|---|---|---|
| `raw/` | 12 CSV originales del dataset sintético (~20 MB). No se editan a mano. | Sí |
| `processed/` | Datos limpios e integrados, features (RFM, etc.) | No (se regeneran) |
| `external/` | Fuentes externas (INEI, feriados, etc.) | No |

Regenerar `raw/`: `python src/data/generar_dataset.py`
