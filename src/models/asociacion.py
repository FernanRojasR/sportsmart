"""Reglas de asociación por subcategoría: comparación de Apriori, FP-Growth y ECLAT.

Salidas: reports/asociacion.json y reports/reglas_asociacion.csv.
Uso:  python -m src.models.asociacion
"""
import json
import statistics
import time
import tracemalloc

import numpy as np
import pandas as pd
from mlxtend.frequent_patterns import apriori, association_rules, fpgrowth

from src.config import PROCESSED, REPORTS

SOPORTE_MIN = 0.01
LIFT_MIN = 1.5
CONFIANZA_MIN = 0.20
INICIO_VALIDACION = pd.Timestamp("2025-10-01")
SOPORTES_COMPARACION = [0.02, 0.01, 0.005, 0.002, 0.001]


def canastas(items: pd.DataFrame, columna: str = "subcategoria") -> pd.DataFrame:
    """Matriz booleana: una fila por pedido válido y una columna por artículo."""
    v = items[items.pedido_valido]
    return pd.crosstab(v.pedido_id, v[columna]).astype(bool)


def eclat(c: pd.DataFrame, min_support: float) -> pd.DataFrame:
    """ECLAT vertical: cada conjunto guarda los pedidos que lo contienen y se extiende por intersección."""
    n, minimo = len(c), min_support * len(c)
    columnas = list(c.columns)
    salida = []

    def extender(prefijo, pedidos, candidatos):
        for pos, (j, m) in enumerate(candidatos):
            inter = pedidos & m if pedidos is not None else m
            k = int(inter.sum())
            if k >= minimo:
                actual = prefijo + [columnas[j]]
                salida.append((k / n, frozenset(actual)))
                extender(actual, inter, candidatos[pos + 1:])

    extender([], None, [(j, c.iloc[:, j].to_numpy()) for j in range(len(columnas))])
    return pd.DataFrame(salida, columns=["support", "itemsets"])


ALGORITMOS = {"Apriori": lambda c, s: apriori(c, min_support=s, use_colnames=True), "FP-Growth": lambda c, s: fpgrowth(c, min_support=s, use_colnames=True), "ECLAT": eclat}


def _firma(fi: pd.DataFrame) -> dict:
    return {i: round(float(s), 10) for i, s in zip(fi.itemsets, fi.support)}


def comparar(c: pd.DataFrame, repeticiones: int = 5) -> list[dict]:
    """Tiempo (mediana), memoria máxima y coincidencia de resultados para cada soporte mínimo."""
    r = []
    for s in SOPORTES_COMPARACION:
        firmas = {}
        for nombre, alg in ALGORITMOS.items():
            tiempos = []
            for _ in range(repeticiones):
                t0 = time.perf_counter(); fi = alg(c, s); tiempos.append(time.perf_counter() - t0)
            tracemalloc.start(); alg(c, s); _, pico = tracemalloc.get_traced_memory(); tracemalloc.stop()
            firmas[nombre] = _firma(fi)
            r.append({"soporte_min": s, "algoritmo": nombre, "conjuntos": len(fi), "segundos": round(statistics.median(tiempos), 4), "memoria_mb": round(pico / 1e6, 2)})
        iguales = firmas["Apriori"] == firmas["FP-Growth"] == firmas["ECLAT"]
        for f in r[-3:]:
            f["resultados_identicos"] = iguales
    return r


def reglas(c: pd.DataFrame, soporte: float = SOPORTE_MIN) -> pd.DataFrame:
    """Reglas con lift y confianza mínimos; marca las que no mejoran a una regla más simple."""
    fi = fpgrowth(c, min_support=soporte, use_colnames=True)
    r = association_rules(fi, metric="lift", min_threshold=LIFT_MIN)
    r = r[r.confidence >= CONFIANZA_MIN].copy()
    r["n_antecedente"] = r.antecedents.map(len)
    previas = {(a, b): conf for a, b, conf in zip(r.antecedents, r.consequents, r.confidence)}
    r["redundante"] = [any(a2 < a and b2 == b and conf <= c2 + 0.01 for (a2, b2), c2 in previas.items()) for a, b, conf in zip(r.antecedents, r.consequents, r.confidence)]
    r["antecedente"] = r.antecedents.map(lambda s: " + ".join(sorted(s))); r["consecuente"] = r.consequents.map(lambda s: " + ".join(sorted(s)))
    columnas = {"support": "soporte", "confidence": "confianza", "antecedent support": "soporte_antecedente", "consequent support": "soporte_consecuente", "lift": "lift", "leverage": "leverage", "conviction": "conviction"}
    r = r.rename(columns=columnas).sort_values(["lift", "confianza"], ascending=False).reset_index(drop=True)
    return r[["antecedente", "consecuente", "n_antecedente", *columnas.values(), "redundante", "antecedents", "consequents"]]


def validar(r: pd.DataFrame, c_prueba: pd.DataFrame) -> pd.DataFrame:
    """Recalcula en pedidos no usados para descubrir las reglas."""
    filas = []
    for a, b in zip(r.antecedents, r.consequents):
        ma, mb = c_prueba[list(a)].all(axis=1), c_prueba[list(b)].all(axis=1)
        sop = float((ma & mb).mean()); conf = sop / float(ma.mean()) if ma.any() else 0.0
        filas.append({"soporte_prueba": sop, "confianza_prueba": conf, "lift_prueba": conf / float(mb.mean()) if mb.any() else 0.0})
    return pd.DataFrame(filas, index=r.index)


def analizar(items: pd.DataFrame) -> tuple[dict, pd.DataFrame]:
    c = canastas(items)
    fechas = items[items.pedido_valido].drop_duplicates("pedido_id").set_index("pedido_id").fecha_pedido.reindex(c.index)
    entrenamiento = fechas < INICIO_VALIDACION
    r_total = reglas(c)
    r_ent = reglas(c[entrenamiento]); v = validar(r_ent, c[~entrenamiento])
    r_ent = r_ent.join(v)
    pares_producto = canastas(items, "producto_id")
    pp = pares_producto.to_numpy(dtype=int); co = pp.T @ pp; np.fill_diagonal(co, 0)
    utiles = r_total[~r_total.redundante]
    exportar = r_total.drop(columns=["antecedents", "consequents"])
    res = {
        "canastas": {"pedidos": len(c), "subcategorias": c.shape[1], "items_por_pedido": round(float(c.sum(axis=1).mean()), 2), "pct_multi_subcategoria": round(100 * float((c.sum(axis=1) > 1).mean()), 1)},
        "nivel_producto": {"productos": pares_producto.shape[1], "soporte_max_producto_pct": round(100 * float(pares_producto.mean().max()), 3), "soporte_max_par_pct": round(100 * float(co.max()) / len(c), 3), "pedidos_max_par": int(co.max())},
        "comparacion": comparar(c),
        "reglas": {"soporte_min": SOPORTE_MIN, "lift_min": LIFT_MIN, "confianza_min": CONFIANZA_MIN, "total": len(r_total), "no_redundantes": len(utiles), "por_tamano_antecedente": {int(k): int(n) for k, n in r_total.n_antecedente.value_counts().sort_index().items()},
                   "lift_max": round(float(r_total.lift.max()), 2), "lift_mediana": round(float(r_total.lift.median()), 2), "confianza_max": round(float(r_total.confianza.max()), 3), "soporte_max_pct": round(100 * float(r_total.soporte.max()), 2)},
        "validacion_temporal": {"pedidos_entrenamiento": int(entrenamiento.sum()), "pedidos_prueba": int((~entrenamiento).sum()), "reglas_entrenamiento": len(r_ent), "se_mantienen_lift": int((r_ent.lift_prueba >= LIFT_MIN).sum()), "se_mantienen_soporte": int((r_ent.soporte_prueba >= SOPORTE_MIN).sum()),
                                "se_mantienen_ambos": int(((r_ent.lift_prueba >= LIFT_MIN) & (r_ent.soporte_prueba >= SOPORTE_MIN)).sum()),
                                "correlacion_lift": round(float(r_ent.lift.corr(r_ent.lift_prueba)), 3), "diferencia_media_confianza": round(float((r_ent.confianza - r_ent.confianza_prueba).abs().mean()), 3)},
        "top_reglas": utiles.head(12)[["antecedente", "consecuente", "soporte", "confianza", "lift"]].round(4).to_dict("records"),
        "top_pares": utiles[utiles.n_antecedente == 1].head(10)[["antecedente", "consecuente", "soporte", "confianza", "lift"]].round(4).to_dict("records"),
    }
    return res, exportar


def main() -> dict:
    items = pd.read_csv(PROCESSED / "ventas_items.csv", parse_dates=["fecha_pedido"], usecols=["pedido_id", "fecha_pedido", "pedido_valido", "subcategoria", "producto_id"])
    res, exportar = analizar(items)
    (REPORTS / "asociacion.json").write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
    exportar.to_csv(REPORTS / "reglas_asociacion.csv", index=False)
    return res


if __name__ == "__main__":
    main()
