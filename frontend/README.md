# frontend

Dashboard para usuarios de negocio. Vistas previstas: segmentos, clientes en riesgo, pronóstico de ventas, reglas de asociación y opiniones.

## Primer prototipo (semanas 10 y 13)

Hecho en Streamlit, con las secciones Resumen, Segmentación, Asociación, Pronóstico, Regresión, Grafos y Evaluación.

```bash
pip install -r requirements.txt
python -m src.pipeline --sin-datos   # necesario para consultar clientes
streamlit run frontend/app.py
```

- `app.py`: páginas del dashboard.
- `datos.py`: carga y consultas, sin dependencias de Streamlit.

Lee los resultados versionados en `reports/`. La consulta por cliente usa `data/processed/segmentos_clientes.csv`, que genera el pipeline. Clasificación, minería de textos, explicabilidad y monitoreo se agregan en la semana 16.
