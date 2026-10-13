<<<<<<< HEAD

=======
# SportSmart Perú · Plataforma Inteligente de Clientes

**Plataforma Inteligente para el Análisis, Segmentación y Predicción de Clientes en el e-commerce de ropa deportiva**

Proyecto del curso **Minería de Datos** — Facultad de Ingeniería de Sistemas e Informática, UNMSM. Metodología **CRISP-DM**.

> Empresa y datos ficticios, con fines académicos.

---

## 💡 Idea del proyecto

SportSmart Perú es una tienda online de ropa y calzado deportivo que registra pedidos, pagos, envíos, campañas, navegación, atención y opiniones de sus clientes, pero solo los usa para reportes descriptivos. El EDA inicial muestra que **71 % de los clientes no compra hace más de 180 días** y que **el 20 % de los clientes genera el 65,5 % de las ventas**.

La plataforma integra 12 fuentes de datos y aplica minería de datos para:

| Pregunta de negocio | Técnica |
|---|---|
| ¿Qué productos se compran juntos? | Reglas de asociación |
| ¿Qué tipos de clientes tenemos? | Clustering |
| ¿Cuánto venderemos? | Series de tiempo |
| ¿Cómo se conectan clientes y productos? | Grafos |
| ¿Cuánto gastará un cliente? | Regresión |
| ¿Quién abandonará? | Clasificación |
| ¿Qué opinan los clientes? | NLP |

📄 Detalle completo (problema, objetivos, alcance, stakeholders, cronograma): [`docs/00_proyecto/idea_proyecto.md`](docs/00_proyecto/idea_proyecto.md)

## 📊 Datos

Dataset sintético integrado: **12 tablas, 472 581 registros** (ene-2023 a sep-2026), con problemas de calidad intencionales para la fase de comprensión de datos. Diccionario de 82 campos en [`docs/02_datos/`](docs/02_datos/).

## 🗂️ Estructura

```
sportsmart/
├── README.md                ← este archivo (idea + guía)
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
│
├── data/
│   ├── raw/                 ← 12 CSV originales (no editar)
│   ├── processed/           ← datos limpios y features
│   └── external/            ← fuentes externas
│
├── notebooks/
│   ├── 01_eda/              ← ✅ 01_eda_calidad.ipynb
│   ├── 02_preparation/
│   ├── 03_association/
│   ├── 04_clustering/
│   ├── 05_timeseries/
│   ├── 06_graphs/
│   ├── 07_regression/
│   ├── 08_classification/
│   └── 09_nlp/
│
├── src/
│   ├── config.py            ← rutas y parámetros comunes
│   ├── pipeline.py          ← ejecuta todo el flujo de datos
│   ├── data/                ← ✅ generar_dataset.py, eda_calidad.py, diccionario.py
│   ├── features/
│   ├── models/
│   ├── evaluation/
│   ├── explainability/
│   └── monitoring/
│
├── backend/                 ← API (api/, services/, models/)
├── frontend/                ← dashboard
├── tests/                   ← ✅ test_datos.py
│
├── docs/
│   ├── 00_proyecto/         ← ✅ idea del proyecto
│   ├── 01_metodologia/      ← ✅ CRISP-DM y criterios de éxito
│   ├── 02_datos/            ← ✅ diccionario de datos
│   ├── 03_presentaciones/   ← diapositivas e informes por semana
│   └── 04_arquitectura/     ← arquitectura de la plataforma
│
├── reports/                 ← ✅ eda.json + figures/
└── deployment/
```

Cada carpeta tiene un `README.md` que explica qué va dentro.

## ▶️ Cómo ejecutar

```bash
pip install -r requirements.txt

python -m src.pipeline              # genera datos + EDA + diccionario
python -m src.pipeline --sin-datos  # solo EDA + diccionario con los CSV actuales
pytest -q                           # pruebas de integridad de datos
jupyter lab                         # abrir notebooks/
```

Con Docker:

```bash
docker compose run --rm pipeline    # pipeline
docker compose up notebooks         # Jupyter en http://localhost:8888
```

## 📅 Avance por entregas

| Semana | Entrega | Fases CRISP-DM | Estado |
|---|---|---|---|
| 7 | Presentación 1 | Comprensión del negocio y de los datos | ✅ |
| 10 | Presentación 2 | Preparación y primeros modelos | ⏳ |
| 13 | Presentación 3 | Modelado y evaluación | ⏳ |
| 16 | Presentación 4 | Despliegue | ⏳ |

## 👥 Equipo

| Integrante | Rol |
|---|---|
| Max Fernando Rojas Rojas | |
| Carrascal Castro Maria Priscila | |
| Gil Sixi Alberto Luis | |

## 📌 Convenciones

- Notebooks numerados: `NN_tema.ipynb` dentro de la carpeta de su técnica.
- Lógica reutilizable en `src/`; los notebooks solo la importan y muestran resultados.
- `data/raw` nunca se modifica; todo lo derivado va a `data/processed`.
- Ramas: `main` (entregas), `dev` (integración), `feature/<tema>` por técnica.
>>>>>>> 8b32112 (Proyecto Sportsmart)
