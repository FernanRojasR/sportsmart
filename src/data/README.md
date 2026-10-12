# src/data

Carga, generación y validación de los datos crudos.

| Script | Qué hace | Salida |
|---|---|---|
| `generar_dataset.py` | Genera el dataset sintético (semilla 42) con errores intencionales | `data/raw/*.csv` |
| `eda_calidad.py` | EDA y diagnóstico de calidad | `reports/eda.json` |
| `diccionario.py` | Diccionario y perfil de las 12 tablas | `docs/02_datos/diccionario_datos.xlsx` |
