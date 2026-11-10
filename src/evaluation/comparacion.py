"""Evaluación comparativa de las técnicas del proyecto.

Consolida los reportes de cada técnica, agrega referencias simples e intervalos de confianza.
Salidas: reports/evaluacion.json y docs/01_metodologia/evaluacion_comparativa.md.
Uso:  python -m src.evaluation.comparacion
"""
import json

import numpy as np
import pandas as pd
from mlxtend.frequent_patterns import association_rules, fpgrowth
from sklearn.metrics import r2_score, silhouette_score

from src.config import DOCS, PROCESSED, REPORTS, SEED
from src.data.estilo_graficos import numero
from src.models.asociacion import CONFIANZA_MIN, LIFT_MIN, SOPORTE_MIN, canastas
from src.models.clustering import MUESTRA_SILUETA, RFM, matriz

REPETICIONES_BOOTSTRAP = 2000
REPETICIONES_AZAR = 5
REF_SERIES = "Referencia (mismo día hace 52 semanas)"
REF_REGRESION = "Referencia (promedio móvil 3 meses)"


def leer(nombre: str) -> dict:
    return json.loads((REPORTS / f"{nombre}.json").read_text(encoding="utf-8"))


def referencia_asociacion(items: pd.DataFrame) -> dict:
    """Reglas que aparecerían si las subcategorías se repartieran al azar entre los pedidos."""
    v = items[items.pedido_valido]; rng = np.random.default_rng(SEED); n = []
    for _ in range(REPETICIONES_AZAR):
        c = canastas(v.assign(subcategoria=rng.permutation(v.subcategoria.values)))
        fi = fpgrowth(c, min_support=SOPORTE_MIN, use_colnames=True)
        if (fi.itemsets.map(len) > 1).any():
            r = association_rules(fi, metric="lift", min_threshold=LIFT_MIN); n.append(int((r.confidence >= CONFIANZA_MIN).sum()))
        else:
            n.append(0)
    return {"reglas_azar_media": round(float(np.mean(n)), 1), "reglas_azar_max": int(np.max(n)), "repeticiones": REPETICIONES_AZAR}


def referencia_clustering(v: pd.DataFrame) -> dict:
    """Alternativa simple: tres grupos iguales según el puntaje RFM total."""
    grupos = pd.qcut(v.rfm_total.rank(method="first"), 3, labels=False)
    return {"silhouette": round(float(silhouette_score(matriz(v, RFM), grupos, sample_size=min(MUESTRA_SILUETA, len(v)), random_state=SEED)), 3)}


def _intervalo(valores: np.ndarray) -> list[float]:
    return [round(float(np.percentile(valores, 2.5)), 3), round(float(np.percentile(valores, 97.5)), 3)]


def bootstrap_series(curva: dict) -> dict:
    """Remuestrea semanas para medir la incertidumbre del MAPE semanal y de su mejora."""
    idx = pd.to_datetime(curva["fechas"])
    def semanal(v):
        g = pd.Series(np.asarray(v, float), idx).resample("W"); return g.sum()[g.count() == 7].to_numpy()
    y, a, b = semanal(curva["real"]), semanal(curva["Prophet"]), semanal(curva[REF_SERIES])
    ea, eb = np.abs((y - a) / y) * 100, np.abs((y - b) / y) * 100
    rng = np.random.default_rng(SEED); m = rng.integers(0, len(y), (REPETICIONES_BOOTSTRAP, len(y)))
    return {"semanas": len(y), "mape_modelo_ic95": _intervalo(ea[m].mean(axis=1)), "mape_referencia_ic95": _intervalo(eb[m].mean(axis=1)), "mejora_puntos_ic95": _intervalo((eb[m] - ea[m]).mean(axis=1))}


def bootstrap_regresion(pred: pd.DataFrame, panel: pd.DataFrame) -> dict:
    """Remuestrea productos completos, porque las filas de un mismo producto no son independientes."""
    d = pred.merge(panel[["producto_id", "mes", "ventas_media_3m"]], on=["producto_id", "mes"])
    grupos = [g[["ventas", "prediccion", "ventas_media_3m"]].to_numpy() for _, g in d.groupby("producto_id")]
    rng = np.random.default_rng(SEED); mod, ref = [], []
    for _ in range(REPETICIONES_BOOTSTRAP):
        a = np.concatenate([grupos[i] for i in rng.integers(0, len(grupos), len(grupos))])
        mod.append(r2_score(a[:, 0], a[:, 1])); ref.append(r2_score(a[:, 0], a[:, 2]))
    mod, ref = np.array(mod), np.array(ref)
    return {"productos": len(grupos), "r2_modelo_ic95": _intervalo(mod), "r2_referencia_ic95": _intervalo(ref), "mejora_r2_ic95": _intervalo(mod - ref)}


def tabla_resultados(r: dict, ref: dict) -> list[dict]:
    a, c, s, g, v = r["asociacion"], r["clustering"], r["series"], r["grafos"], r["regresion"]["ventas"]
    km = c["comparacion"]["K-Means RFM (k=3)"]["silhouette"]; p = s["prueba_6_meses"]["Prophet"]; co = g["comunidades"]; mv = v["modelos"][v["mejor_modelo"]]
    filas = [
        {"tecnica": "Asociación", "modelo": "FP-Growth, por subcategoría", "metrica": "Reglas con lift > 1,5 y soporte ≥ 1 %", "resultado": a["reglas"]["total"], "meta": "Al menos 1 regla", "cumple": a["reglas"]["total"] >= 1, "referencia": ref["asociacion"]["reglas_azar_media"], "referencia_nombre": "Canastas al azar", "mejor_si": "mayor", "validacion": f"{a['validacion_temporal']['se_mantienen_lift']} de {a['validacion_temporal']['reglas_entrenamiento']} reglas mantienen el lift en el año siguiente"},
        {"tecnica": "Clustering", "modelo": "K-Means sobre RFM, 3 segmentos", "metrica": "Silhouette", "resultado": km, "meta": "> 0,4", "cumple": km > .4, "referencia": ref["clustering"]["silhouette"], "referencia_nombre": "Tercios de puntaje RFM", "mejor_si": "mayor", "validacion": f"ARI de {numero(c['estabilidad_k3']['ari_medio_submuestras'], 3)} con submuestras de 80 %"},
        {"tecnica": "Series temporales", "modelo": "Prophet con calendario y campañas", "metrica": "MAPE semanal (%)", "resultado": p["mape_semanal"], "meta": "< 15 %", "cumple": p["mape_semanal"] < 15, "referencia": s["prueba_6_meses"][REF_SERIES]["mape_semanal"], "referencia_nombre": "Mismo día hace 52 semanas", "mejor_si": "menor", "validacion": "Últimos 6 meses, 4 orígenes y temporada alta 2025"},
        {"tecnica": "Grafos", "modelo": "Louvain sobre producto-producto", "metrica": "Modularidad", "resultado": co["modularidad"], "meta": "> 0,3", "cumple": co["modularidad"] > .3, "referencia": co["referencia_azar"]["modularidad_media"], "referencia_nombre": "Compras al azar", "mejor_si": "mayor", "validacion": f"ARI de {numero(co['estabilidad']['ari_medio'], 3)} entre semillas"},
        {"tecnica": "Regresión", "modelo": f"{v['mejor_modelo']}, por producto y mes", "metrica": "R²", "resultado": mv["r2"], "meta": "> 0,6", "cumple": mv["r2"] > .6, "referencia": v["modelos"][REF_REGRESION]["r2"], "referencia_nombre": "Promedio móvil 3 meses", "mejor_si": "mayor", "validacion": "Abril a setiembre de 2026, con hiperparámetros validados en el pasado"},
    ]
    for f in filas:
        f["supera_referencia"] = f["resultado"] > f["referencia"] if f["mejor_si"] == "mayor" else f["resultado"] < f["referencia"]
    return filas


def metas_no_alcanzadas(r: dict) -> list[dict]:
    p, vc, c = r["series"]["prueba_6_meses"]["Prophet"], r["regresion"]["valor_cliente"]["modelos"]["Random Forest"], r["clustering"]["productos"]
    return [{"analisis": "MAPE diario de ventas", "resultado": f"{numero(p['mape_diario'], 2)} %", "referencia_meta": "< 15 %", "causa": "Las ventas de cada día son muy variables", "decision": "Usar el pronóstico para planificar por semana o periodo"},
            {"analisis": "Gasto futuro del cliente", "resultado": f"R² medio de {numero(vc['r2_medio'], 3)}", "referencia_meta": "R² > 0,6", "causa": f"{numero(r['regresion']['valor_cliente']['pct_gasto_futuro_cero'])} % de los compradores no gasta en los 12 meses siguientes", "decision": "Análisis secundario; evaluar un modelo de dos etapas con el de abandono"},
            {"analisis": "Agrupación de productos", "resultado": f"Silhouette de {numero(c['silhouette']['silhouette'], 3)}", "referencia_meta": "Sin meta propia; 0,4 en clientes", "causa": "Los productos no forman grupos bien separados", "decision": "Usar ABC/XYZ para decisiones de producto"}]


def respuestas(r: dict) -> list[dict]:
    a, c, s, g, reg = r["asociacion"], r["clustering"], r["series"], r["grafos"], r["regresion"]
    per = {p["segmento"]: p for p in c["perfil_segmentos"]}; fut = s["pronostico_futuro"]; v = reg["ventas"]; co = g["comunidades"]["perfil"]; top = a["top_pares"][0]
    pct = lambda x: numero(x) + " %"
    return [
        {"n": "1", "pregunta": "¿Qué segmentos de clientes existen?", "respuesta": "Tres: Alto valor activos, Valiosos inactivos y Ocasionales inactivos."},
        {"n": "2", "pregunta": "¿Qué clientes presentan mayor valor?", "respuesta": f"Alto valor activos: {pct(per['Alto valor activos']['pct_clientes'])} de los compradores y mediana de CLV de S/ {numero(per['Alto valor activos']['clv'], 0)}. Valiosos inactivos aportó {pct(per['Valiosos inactivos']['pct_ventas'])} de las ventas históricas."},
        {"n": "3", "pregunta": "¿Qué clientes presentan características similares?", "respuesta": f"Los de cada segmento y comunidad; {pct(g['clientes_relacionados']['vecino_comparte_deporte_pct'])} comparte deporte con su cliente más parecido."},
        {"n": "4", "pregunta": "¿Cómo evolucionan las ventas?", "respuesta": f"Crecen y son estacionales; los días de quincena venden {numero((s['descomposicion']['efecto_quincena'] - 1) * 100, 0)} % más."},
        {"n": "5", "pregunta": "¿Cuál es la tendencia futura de las ventas?", "respuesta": f"Se esperan S/ {numero(fut['90']['pronostico'], 0)} en 90 días, {numero((fut['90']['pronostico'] / fut['90']['mismo_periodo_anio_anterior'] - 1) * 100)} % sobre el mismo periodo anterior."},
        {"n": "6", "pregunta": "¿Qué factores explican las ventas?", "respuesta": "Domina el historial de ventas; luego precio y costo, y campañas. Las visitas no agregan capacidad predictiva."},
        {"n": "7", "pregunta": "¿Qué productos se compran conjuntamente?", "respuesta": f"Por subcategoría, por ejemplo {top['antecedente']} y {top['consecuente']}."},
        {"n": "8", "pregunta": "¿Qué productos tienen mayor asociación?", "respuesta": f"{a['reglas']['total']} reglas superan la meta; el lift máximo es {numero(a['reglas']['lift_max'], 2)}."},
        {"n": "9", "pregunta": "¿Qué productos presentan comportamientos similares?", "respuesta": "Dos grupos débiles de alta y baja rotación; ABC/XYZ resulta más útil."},
        {"n": "10", "pregunta": "¿Cuál será el volumen de ventas esperado?", "respuesta": f"Por producto y mes, con R² de {numero(v['modelos'][v['mejor_modelo']]['r2'], 3)}; el error total mensual es de {pct(v['total_mensual']['wape_pct'])}."},
        {"n": "11", "pregunta": "¿Cuánto gastará un cliente?", "respuesta": f"Solo aproximado: R² medio de {numero(reg['valor_cliente']['modelos']['Random Forest']['r2_medio'], 3)}, bajo la meta."},
        {"n": "14", "pregunta": "¿Qué productos, clientes o categorías están fuertemente conectados?", "respuesta": "Destacan los Tomatodos como conectores. Entre categorías, solo Calzado y Accesorios."},
        {"n": "15", "pregunta": "¿Qué comunidades o patrones pueden encontrarse?", "respuesta": f"Tres comunidades: Running y fútbol ({numero(co[0]['ingresos_pct'])} % de ingresos), Training y yoga ({numero(co[1]['ingresos_pct'])} %) y Outdoor ({numero(co[2]['ingresos_pct'])} %)."},
    ]


KPIS = [("Asociación", "V2 Ticket promedio; M2 Conversión de campañas; M3 Carritos abandonados", "Paquetes y recomendaciones"),
        ("Clustering", "C1 Activación; M1 CTR; M2 Conversión", "Campañas distintas por segmento"),
        ("Series temporales", "V1 Crecimiento; I1, I2 e I3 Quiebres y excesos", "Compras anticipadas para la temporada alta"),
        ("Grafos", "M3 Carritos abandonados; V2 Ticket promedio", "Recomendaciones por comunidad deportiva"),
        ("Regresión", "I1 e I3 Quiebres y excesos", "Estimar la demanda de cada producto")]


def _valor(f: dict) -> tuple[str, str]:
    if f["tecnica"] == "Asociación":
        return str(f["resultado"]), numero(f["referencia"])
    d = 2 if f["tecnica"] == "Series temporales" else 3
    return numero(f["resultado"], d), numero(f["referencia"], d)


def _ic(v: list[float], d: int = 3) -> str:
    return f"{numero(v[0], d)} a {numero(v[1], d)}"


def markdown(res: dict, r: dict) -> str:
    t = res["resultados"]; b = res["bootstrap"]
    s = ["# Evaluación comparativa — SportSmart Perú", "", "Fase CRISP-DM: **Evaluación**. Cubre las técnicas de las semanas 10 y 13. Este documento se genera con `python -m src.evaluation.comparacion` a partir de los reportes de cada técnica.", "", "## 1. Resumen", "",
         f"**{sum(f['cumple'] for f in t)} de {len(t)} técnicas** cumplen su meta y **{sum(f['supera_referencia'] for f in t)} de {len(t)}** superan a su referencia simple. {len(res['no_alcanzadas'])} análisis complementarios no alcanzan el nivel esperado y se reportan en la sección 4.", "", "> Los datos son simulados: estos resultados evalúan el método y reflejan patrones incorporados al generar el dataset. No demuestran un impacto real en el negocio.", "",
         "## 2. Resultados frente a metas y referencias", "", "| Técnica | Modelo elegido | Métrica | Resultado | Meta | ¿Cumple? | Referencia simple | Valor de referencia | Validación |", "|---|---|---|---|---|---|---|---|---|"]
    for f in t:
        a, c = _valor(f); s.append(f"| {f['tecnica']} | {f['modelo']} | {f['metrica']} | {a} | {f['meta']} | {'Sí' if f['cumple'] else 'No'} | {f['referencia_nombre']} | {c} | {f['validacion']} |")
    bs, br = b["series"], b["regresion"]
    s += ["", "## 3. ¿La mejora sobre la referencia es real?", "", "Intervalos de confianza de 95 % obtenidos por remuestreo (bootstrap). Si el intervalo de mejora no incluye el cero, la diferencia no se explica por azar en el periodo evaluado.", "",
          "| Técnica | Modelo | Referencia | Mejora |", "|---|---|---|---|", f"| Series temporales (MAPE semanal, %) | {_ic(bs['mape_modelo_ic95'], 2)} | {_ic(bs['mape_referencia_ic95'], 2)} | {_ic(bs['mejora_puntos_ic95'], 2)} puntos |", f"| Regresión (R²) | {_ic(br['r2_modelo_ic95'])} | {_ic(br['r2_referencia_ic95'])} | {_ic(br['mejora_r2_ic95'])} |", "",
          f"En series temporales, el límite inferior de la mejora es de solo {numero(bs['mejora_puntos_ic95'][0], 2)} puntos: Prophet probablemente es mejor que la referencia, pero con {bs['semanas']} semanas esa ventaja es incierta. En regresión, con {br['productos']} productos, la mejora es más clara.", "",
          f"En asociación, las canastas al azar generan en promedio {numero(res['referencias']['asociacion']['reglas_azar_media'])} reglas; en grafos, la modularidad con compras al azar no supera {numero(r['grafos']['comunidades']['referencia_azar']['modularidad_max'], 3)}.", "",
          "## 4. Resultados que no alcanzan lo esperado", "", "| Análisis | Resultado | Esperado | Causa | Decisión |", "|---|---|---|---|---|"]
    s += [f"| {m['analisis']} | {m['resultado']} | {m['referencia_meta']} | {m['causa']} | {m['decision']} |" for m in res["no_alcanzadas"]]
    a, c, se, g, v = r["asociacion"], r["clustering"], r["series"], r["grafos"], r["regresion"]["ventas"]
    s += ["", "## 5. Comparación dentro de cada técnica", "", "### Asociación (soporte mínimo 1 %)", "", "| Algoritmo | Conjuntos | Memoria máxima (MB) | Resultados idénticos |", "|---|---|---|---|"]
    s += [f"| {x['algoritmo']} | {x['conjuntos']} | {numero(x['memoria_mb'], 2)} | {'Sí' if x['resultados_identicos'] else 'No'} |" for x in a["comparacion"] if x["soporte_min"] == .01]
    s += ["", "### Clustering", "", "| Algoritmo | Silhouette | Davies-Bouldin | Grupos | Ruido (%) |", "|---|---|---|---|---|"]
    s += [f"| {k.replace('0.', '0,')} | {numero(x['silhouette'], 3)} | {numero(x['davies_bouldin'], 3)} | {int(x['grupos'])} | {numero(x['ruido_pct'])} |" for k, x in c["comparacion"].items()]
    s += ["", "### Series temporales", "", "| Modelo | MAPE semanal (%) | MAPE diario (%) | MAPE semanal en temporada alta (%) |", "|---|---|---|---|"]
    s += [f"| {m} | {numero(x['mape_semanal'], 2)} | {numero(x['mape_diario'], 2)} | {numero(se['temporada_alta_2025']['metricas'][m]['mape_semanal'], 2)} |" for m, x in sorted(se["prueba_6_meses"].items(), key=lambda kv: kv[1]["mape_semanal"])]
    s += ["", "### Grafos", "", "| Red | Modularidad |", "|---|---|", f"| Producto-producto, 5 o más pedidos en común | {numero(g['comunidades']['modularidad'], 3)} |", f"| Producto-producto, todas las conexiones | {numero(g['producto_producto']['modularidad_sin_umbral'], 3)} |", f"| Compras al azar (promedio) | {numero(g['comunidades']['referencia_azar']['modularidad_media'], 3)} |"]
    s += ["", "### Regresión", "", "| Modelo | R² de validación | R² de prueba | RMSE (S/) | WAPE (%) |", "|---|---|---|---|---|"]
    for m, x in v["modelos"].items():
        s.append(f"| {m}{' (elegido)' if m == v['mejor_modelo'] else ''} | {numero(x['r2_validacion'], 3) if 'r2_validacion' in x else '—'} | {numero(x['r2'], 3)} | {numero(x['rmse'])} | {numero(x['wape_pct'])} |")
    s += ["", "El modelo se eligió por su resultado de validación. Ridge, Lasso y la regresión múltiple obtienen un R² de prueba algo mayor, con diferencias pequeñas.", "", "## 6. Respuestas a las preguntas de negocio", "", "La numeración corresponde a `docs/00_proyecto/idea_proyecto.md`. Las preguntas 12, 13, 16, 17 y 18 se abordan en la semana 16.", "", "| N.° | Pregunta | Respuesta |", "|---|---|---|"]
    s += [f"| {x['n']} | {x['pregunta']} | {x['respuesta']} |" for x in res["respuestas"]]
    s += ["", "## 7. Relación con los KPIs de negocio", "", "Los modelos ofrecen herramientas para mejorar estos indicadores. Con datos simulados no se puede medir su efecto real.", "", "| Técnica | KPIs relacionados | Uso propuesto |", "|---|---|---|"]
    s += [f"| {a_} | {b_} | {c_} |" for a_, b_, c_ in KPIS]
    return "\n".join(s) + "\n"


def evaluar(r: dict, items: pd.DataFrame, clientes: pd.DataFrame, pred: pd.DataFrame, panel: pd.DataFrame) -> dict:
    ref = {"asociacion": referencia_asociacion(items), "clustering": referencia_clustering(clientes)}
    return {"resultados": tabla_resultados(r, ref), "referencias": ref, "bootstrap": {"series": bootstrap_series(r["series"]["curva_prueba"]), "regresion": bootstrap_regresion(pred, panel)}, "no_alcanzadas": metas_no_alcanzadas(r), "respuestas": respuestas(r)}


def main() -> dict:
    r = {n: leer(n) for n in ("asociacion", "clustering", "series", "grafos", "regresion")}
    items = pd.read_csv(PROCESSED / "ventas_items.csv", usecols=["pedido_id", "subcategoria", "pedido_valido"])
    res = evaluar(r, items, pd.read_csv(PROCESSED / "clientes_variables.csv"), pd.read_csv(REPORTS / "predicciones_regresion.csv"), pd.read_csv(PROCESSED / "panel_producto_mes.csv"))
    (REPORTS / "evaluacion.json").write_text(json.dumps(res, ensure_ascii=False, indent=1, default=lambda x: bool(x) if isinstance(x, np.bool_) else float(x)), encoding="utf-8")
    (DOCS / "01_metodologia" / "evaluacion_comparativa.md").write_text(markdown(res, r), encoding="utf-8")
    return res


if __name__ == "__main__":
    main()
