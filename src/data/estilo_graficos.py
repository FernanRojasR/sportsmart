"""Estilo común de los gráficos del proyecto.

Azul para la serie principal y naranja solo para resaltar lo importante.
"""
from pathlib import Path

import matplotlib.pyplot as plt

from src.config import FIGURES

AZUL = "#2a78d6"
NARANJA = "#eb6834"
AZULES_ORDEN = ["#86b6ef", "#2a78d6", "#184f95"]  # categorías ordenadas (claro a oscuro)
GRIS = "#c3c2b7"
SUPERFICIE = "#fcfcfb"
TINTA = "#0b0b0b"
TINTA_2 = "#52514e"
TENUE = "#898781"
REJILLA = "#e1e0d9"
DIVERGENTE = ["#2a78d6", "#f0efec", "#e34948"]


def aplicar_estilo() -> None:
    plt.rcParams.update({
        "figure.facecolor": SUPERFICIE, "axes.facecolor": SUPERFICIE, "savefig.facecolor": SUPERFICIE,
        "font.family": "sans-serif", "font.sans-serif": ["Segoe UI", "DejaVu Sans", "Arial"], "font.size": 10,
        "axes.edgecolor": GRIS, "axes.linewidth": 0.8, "axes.spines.top": False, "axes.spines.right": False,
        "axes.spines.left": False, "axes.grid": True, "axes.grid.axis": "y", "grid.color": REJILLA, "grid.linewidth": 0.7,
        "axes.axisbelow": True, "axes.titlelocation": "left", "axes.titlesize": 12, "axes.titleweight": "bold",
        "axes.titlecolor": TINTA, "axes.labelcolor": TINTA_2, "xtick.color": TENUE, "ytick.color": TENUE,
        "xtick.labelcolor": TINTA_2, "ytick.labelcolor": TINTA_2, "xtick.major.size": 0, "ytick.major.size": 0,
        "legend.frameon": False, "figure.dpi": 100,
    })


def numero(valor: float, decimales: int = 1) -> str:
    """Formato peruano del informe: 13 968 142 y 70,9."""
    return f"{valor + 0.0:,.{decimales}f}".replace(",", " ").replace(".", ",")  # + 0.0 evita "-0,00"


def barras_h(ax, etiquetas, valores, colores=AZUL, formato=lambda v: numero(v)) -> None:
    """Barras horizontales delgadas con el valor al final de cada barra."""
    pos = range(len(etiquetas))
    ax.barh(list(pos), valores, height=0.58, color=colores)
    ax.set_yticks(list(pos), etiquetas)
    ax.invert_yaxis()
    ax.grid(False)
    ax.spines["bottom"].set_visible(False)
    ax.set_xticks([])
    maximo = max(valores)
    ax.set_xlim(0, maximo * 1.16)
    for i, v in enumerate(valores):
        ax.text(v + maximo * 0.012, i, formato(v), va="center", color=TINTA, fontsize=9.5)


def guardar(fig, nombre: str, carpeta: Path = FIGURES) -> None:
    carpeta.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(carpeta / f"{nombre}.png", dpi=150)
    plt.show()
