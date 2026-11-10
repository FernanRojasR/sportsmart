"""Gráficos de la evaluación comparativa y de la regresión para presentaciones e informes.

Salidas en reports/figures: regresion_validacion_prueba.png, regresion_factores_detalle.png y evaluacion_comparativa.png.
Uso:  python -m src.evaluation.graficos
"""
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.lines import Line2D  # noqa: E402

from src.config import FIGURES, REPORTS  # noqa: E402
from src.data.estilo_graficos import AZUL, GRIS, NARANJA, SUPERFICIE, TENUE, TINTA, TINTA_2, aplicar_estilo, numero  # noqa: E402

REFERENCIA_REGRESION = "Referencia (promedio móvil 3 meses)"


def _leer(nombre: str) -> dict:
    return json.loads((REPORTS / f"{nombre}.json").read_text(encoding="utf-8"))


def _guardar(fig, carpeta: Path, nombre: str) -> Path:
    carpeta.mkdir(parents=True, exist_ok=True)
    ruta = carpeta / f"{nombre}.png"
    fig.tight_layout(); fig.savefig(ruta, dpi=200); plt.close(fig)
    return ruta


def regresion_validacion_prueba(reg: dict, carpeta: Path = FIGURES) -> Path:
    """R² de validación y de prueba por modelo: muestra por qué se eligió el modelo."""
    v = reg["ventas"]; elegido = v["mejor_modelo"]; meta = v["meta_r2"]
    modelos = list(v["modelos"].items())
    fig, ax = plt.subplots(figsize=(10, 5.2)); ax.grid(axis="x"); ax.grid(axis="y", visible=False)
    for i, (nombre, m) in enumerate(modelos):
        val = m.get("r2_validacion")
        if val is not None:
            ax.plot([val, m["r2"]], [i, i], color=GRIS, lw=2, zorder=1)
            ax.scatter([val], [i], s=70, color=AZUL, edgecolor=SUPERFICIE, linewidth=1.5, zorder=3)
        ax.scatter([m["r2"]], [i], s=70, color=NARANJA, edgecolor=SUPERFICIE, linewidth=1.5, zorder=3)
        ax.text(m["r2"] + .004, i, numero(m["r2"], 3), va="center", fontsize=9.5, color=TINTA)
    ax.axvline(meta, color=TENUE, lw=1.2); ax.text(meta + .003, -.75, f"Meta {numero(meta, 1)}", fontsize=9.5, color=TINTA_2, va="center")
    etiquetas = [n.replace(REFERENCIA_REGRESION, "Referencia (promedio móvil)") + (" (elegido)" if n == elegido else "") for n, _ in modelos]
    ax.set_yticks(range(len(modelos)), etiquetas); ax.set_ylim(len(modelos) - .5, -1.1)
    for t, (n, _) in zip(ax.get_yticklabels(), modelos):
        if n == elegido:
            t.set_fontweight("bold"); t.set_color(TINTA)
    ax.set_xlim(.58, .79); ax.set_xticks([.60, .65, .70, .75]); ax.set_xlabel("R²"); ax.xaxis.set_major_formatter(lambda x, _: numero(x, 2))
    ax.legend(handles=[Line2D([], [], marker="o", ls="", color=AZUL, label="Validación (elige el modelo)"), Line2D([], [], marker="o", ls="", color=NARANJA, label="Prueba (abr-set 2026)")], loc="lower left", bbox_to_anchor=(0, 1.0), ncol=2, borderaxespad=0.2)
    ax.set_title(f"{elegido} tuvo el mejor R² de validación; en prueba todos superan la meta", pad=30)
    return _guardar(fig, carpeta, "regresion_validacion_prueba")


def regresion_factores_detalle(reg: dict, carpeta: Path = FIGURES) -> Path:
    """Caída de R² por grupo de variables, con un acercamiento a los factores menores."""
    b = reg["ventas"]["importancia_bloques"]; nombres, valores = list(b), list(b.values())
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(11.5, 3.9), gridspec_kw={"width_ratios": [1, 1.15]})
    for ax, n, v, titulo, color in ((a1, nombres, valores, "Todos los grupos", [NARANJA] + [AZUL] * (len(nombres) - 1)), (a2, nombres[1:], valores[1:], "Acercamiento sin el historial", AZUL)):
        ax.barh(range(len(n)), v, height=.58, color=color); ax.set_yticks(range(len(n)), n); ax.invert_yaxis()
        ax.grid(False); ax.spines["bottom"].set_visible(False); ax.set_xticks([]); ax.set_xlim(0, max(v) * 1.22)
        for i, x in enumerate(v):
            ax.text(x + max(v) * .015, i, numero(x, 3), va="center", fontsize=9.5, color=TINTA)
        ax.set_title(titulo, fontsize=11)
    fig.suptitle("El historial de ventas domina; precio y campañas aportan algo (caída de R² al quitar cada grupo)", x=.01, ha="left", fontsize=12, fontweight="bold", color=TINTA)
    return _guardar(fig, carpeta, "regresion_factores_detalle")


def evaluacion_comparativa(ev: dict, carpeta: Path = FIGURES) -> Path:
    """Un panel por técnica: modelo elegido frente a la referencia simple y la meta."""
    metas = {"Asociación": 1, "Clustering": .4, "Series temporales": 15, "Grafos": .3, "Regresión": .6}
    metricas = {"Asociación": "Reglas (lift > 1,5)", "Clustering": "Silhouette", "Series temporales": "MAPE semanal (%)", "Grafos": "Modularidad", "Regresión": "R²"}
    ic = {"Series temporales": (ev["bootstrap"]["series"]["mape_modelo_ic95"], ev["bootstrap"]["series"]["mape_referencia_ic95"]), "Regresión": (ev["bootstrap"]["regresion"]["r2_modelo_ic95"], ev["bootstrap"]["regresion"]["r2_referencia_ic95"])}
    filas = ev["resultados"]
    fig, axes = plt.subplots(1, len(filas), figsize=(13.5, 4.3))
    for ax, f in zip(axes, filas):
        t = f["tecnica"]; d = 0 if t == "Asociación" else 2 if t == "Series temporales" else 3
        vals = [f["resultado"], f["referencia"]]
        ax.bar([0, 1], vals, width=.6, color=[AZUL, GRIS])
        if t in ic:
            for x, (lo, hi) in zip((0, 1), ic[t]):
                ax.plot([x, x], [lo, hi], color=TINTA, lw=1.2); ax.plot([x - .08, x + .08], [lo, lo], color=TINTA, lw=1.2); ax.plot([x - .08, x + .08], [hi, hi], color=TINTA, lw=1.2)
        tope = max(vals + [metas[t]] + ([ic[t][1][1]] if t in ic else [])) * 1.25
        ax.axhline(metas[t], color=NARANJA, lw=1.4, ls=(0, (4, 3)))
        for x, v in zip((0, 1), vals):
            alto = ic[t][x][1] if t in ic else v
            ax.text(x, alto + tope * .02, numero(v, d), ha="center", va="bottom", fontsize=10, color=TINTA, fontweight="bold" if x == 0 else "normal")
        ax.set_ylim(0, tope); ax.set_xlim(-.55, 1.55); ax.set_xticks([0, 1], ["Modelo", "Referencia"]); ax.set_yticks([]); ax.grid(False)
        ax.set_title(f"{t}\n{metricas[t]}\nMeta: {f['meta']}" + (" (menor es mejor)" if f["mejor_si"] == "menor" else ""), fontsize=10.5)
    fig.suptitle("Las cinco técnicas cumplen su meta y superan a su referencia simple", x=.01, ha="left", fontsize=13, fontweight="bold", color=TINTA)
    fig.text(.01, .005, "Barras verticales: intervalo de confianza de 95 % por remuestreo. Línea discontinua: meta de cada técnica. Datos simulados.", fontsize=8.5, color=TINTA_2)
    return _guardar(fig, carpeta, "evaluacion_comparativa")


def main(carpeta: Path = FIGURES) -> list[Path]:
    aplicar_estilo()
    reg, ev = _leer("regresion"), _leer("evaluacion")
    return [regresion_validacion_prueba(reg, carpeta), regresion_factores_detalle(reg, carpeta), evaluacion_comparativa(ev, carpeta)]


if __name__ == "__main__":
    for r in main():
        print(r.name)
