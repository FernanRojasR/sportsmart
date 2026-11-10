"""Carga y consultas del prototipo. Sin dependencias de Streamlit, para poder probarlo."""
import json
import sys
from pathlib import Path

import pandas as pd

RAIZ = Path(__file__).resolve().parents[1]
if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))

from src.config import FIGURES, PROCESSED, REPORTS  # noqa: E402

COMUNIDADES = {0: "Running y fútbol", 1: "Training y yoga", 2: "Outdoor"}
HORIZONTES = (7, 30, 60, 90)


def leer_json(nombre: str) -> dict:
    return json.loads((REPORTS / f"{nombre}.json").read_text(encoding="utf-8"))


def leer_reporte_csv(nombre: str, **kwargs) -> pd.DataFrame:
    return pd.read_csv(REPORTS / f"{nombre}.csv", **kwargs)


def leer_segmentos() -> pd.DataFrame | None:
    """Tabla no versionada: existe solo tras ejecutar el pipeline."""
    ruta = PROCESSED / "segmentos_clientes.csv"
    return pd.read_csv(ruta) if ruta.exists() else None


def figura(nombre: str) -> Path:
    return FIGURES / f"{nombre}.png"


def buscar_cliente(segmentos: pd.DataFrame, cliente_id: str) -> pd.Series | None:
    fila = segmentos[segmentos.cliente_id == cliente_id.strip().upper()]
    return None if fila.empty else fila.iloc[0]


def subcategorias_con_reglas(reglas: pd.DataFrame) -> list[str]:
    return sorted({p for a in reglas.antecedente for p in a.split(" + ")})


def recomendaciones(reglas: pd.DataFrame, subcategoria: str, lift_min: float = 1.5) -> pd.DataFrame:
    """Reglas no redundantes de un solo antecedente para la subcategoría elegida."""
    r = reglas[(reglas.antecedente == subcategoria) & ~reglas.redundante & (reglas.lift >= lift_min)]
    return r.sort_values("lift", ascending=False)[["consecuente", "soporte", "confianza", "lift"]].reset_index(drop=True)


def resumen_horizonte(series: dict, horizonte: int) -> dict:
    f = series["pronostico_futuro"][str(horizonte)]
    return {**f, "variacion_pct": 100 * (f["pronostico"] / f["mismo_periodo_anio_anterior"] - 1)}


def pronostico_hasta(tabla: pd.DataFrame, horizonte: int) -> pd.DataFrame:
    return tabla.iloc[:horizonte]


def real_vs_prediccion(pred: pd.DataFrame, categoria: str | None = None, producto: str | None = None) -> pd.DataFrame:
    d = pred
    if categoria:
        d = d[d.categoria == categoria]
    if producto:
        d = d[d.producto_id == producto]
    return d.groupby("mes", as_index=False)[["ventas", "prediccion"]].sum()


def productos_comunidad(nodos: pd.DataFrame, comunidad: int, n: int = 10) -> pd.DataFrame:
    return nodos[nodos.comunidad == comunidad].sort_values("pagerank", ascending=False).head(n)[["producto_id", "subcategoria", "categoria", "grado", "fuerza", "pagerank"]].reset_index(drop=True)
