"""Rutas y parámetros compartidos del proyecto SportSmart.

Uso:  from src.config import RAW, PROCESSED, REPORTS
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

DATA = ROOT / "data"
RAW = DATA / "raw"              # datos originales (no se modifican)
PROCESSED = DATA / "processed"  # datos limpios / features listos para modelar
EXTERNAL = DATA / "external"    # fuentes externas (INEI, feriados, clima, etc.)

DOCS = ROOT / "docs"
REPORTS = ROOT / "reports"
FIGURES = REPORTS / "figures"
MODELS_DIR = ROOT / "src" / "models" / "artifacts"  # modelos entrenados (.pkl / .joblib)

SEED = 42
FECHA_CORTE = "2026-09-30"  # cierre del periodo de análisis

TABLAS = [
    "clientes", "productos", "pedidos", "detalle_pedido", "pagos", "campanias",
    "marketing", "navegacion", "atencion", "opiniones", "devoluciones", "logistica",
]
