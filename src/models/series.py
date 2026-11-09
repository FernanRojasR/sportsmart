"""Pronóstico de ventas diarias: referencia estacional, SARIMA, SARIMAX y Prophet.

Salidas: reports/series.json y reports/pronostico_ventas.csv.
Uso:  python -m src.models.series
"""
import itertools
import json
import logging
import warnings

import numpy as np
import pandas as pd
from statsmodels.tsa.seasonal import STL
from statsmodels.tsa.statespace.sarimax import SARIMAX
from statsmodels.tsa.stattools import adfuller

from src.config import PROCESSED, REPORTS, SEED

logging.getLogger("prophet").setLevel(logging.ERROR)

DIAS_PRUEBA = 180
HORIZONTES = (7, 30, 60, 90)
PASO_ORIGENES = 30
ORIGEN_TEMPORADA_ALTA = pd.Timestamp("2025-10-01")
META_MAPE = 15.0
MODELOS = ("Referencia (mismo día hace 52 semanas)", "SARIMA", "SARIMAX", "Prophet")
ORDEN_ESTACIONAL = (0, 1, 1, 7)
REJILLA_ORDEN = list(itertools.product((0, 1, 2), (0,), (0, 1, 2)))


def cargar() -> pd.DataFrame:
    return pd.read_csv(PROCESSED / "serie_diaria.csv", parse_dates=["fecha"]).set_index("fecha").asfreq("D")


def calendario(idx: pd.DatetimeIndex, descuento: pd.Series) -> pd.DataFrame:
    """Variables conocidas de antemano: quincenas, campañas y estacionalidad anual (Fourier)."""
    x = pd.DataFrame(index=idx)
    x["quincena"] = idx.day.isin([1, 15, 16, 30, 31]).astype(float)
    x["descuento_campania"] = descuento.reindex(idx).values
    for k in (1, 2, 3):
        ang = 2 * np.pi * k * idx.day_of_year.values / 365.25
        x[f"sen{k}"], x[f"cos{k}"] = np.sin(ang), np.cos(ang)
    return x


def _ajustar_sarimax(y, ex, orden):
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        return SARIMAX(np.log1p(y), exog=ex, order=orden, seasonal_order=ORDEN_ESTACIONAL, enforce_stationarity=False, enforce_invertibility=False).fit(disp=False, maxiter=100)


def elegir_orden(y: pd.Series, ex: pd.DataFrame | None) -> tuple[tuple, list[dict]]:
    """Orden con menor AIC, usando solo entrenamiento."""
    tabla = []
    for o in REJILLA_ORDEN:
        tabla.append({"orden": list(o), "aic": round(float(_ajustar_sarimax(y, ex, o).aic), 1)})
    mejor = min(tabla, key=lambda r: r["aic"])
    return tuple(mejor["orden"]), sorted(tabla, key=lambda r: r["aic"])[:5]


def _prophet(y: pd.Series, ex: pd.DataFrame, muestras: int = 0):
    from prophet import Prophet
    m = Prophet(yearly_seasonality=True, weekly_seasonality=True, daily_seasonality=False, seasonality_mode="multiplicative", uncertainty_samples=muestras)
    for c in ("quincena", "descuento_campania"):
        m.add_regressor(c, mode="multiplicative")
    df = pd.DataFrame({"ds": y.index, "y": y.values, "quincena": ex.quincena.values, "descuento_campania": ex.descuento_campania.values})
    logging.getLogger("cmdstanpy").setLevel(logging.ERROR)  # Prophet lo reconfigura al crear el modelo
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        m.fit(df, seed=SEED)
    return m


def _futuro(ex: pd.DataFrame) -> pd.DataFrame:
    return pd.DataFrame({"ds": ex.index, "quincena": ex.quincena.values, "descuento_campania": ex.descuento_campania.values})


def pronosticar(modelo: str, y: pd.Series, ex: pd.DataFrame, ex_fut: pd.DataFrame, ordenes: dict) -> np.ndarray:
    n = len(ex_fut)
    if modelo == MODELOS[0]:
        serie = y.copy()
        return np.array([serie.get(d - pd.Timedelta(days=364), np.nan) if d - pd.Timedelta(days=364) in serie.index else np.nan for d in ex_fut.index])
    if modelo == "SARIMA":
        return np.expm1(_ajustar_sarimax(y, None, ordenes["SARIMA"]).forecast(n).values)
    if modelo == "SARIMAX":
        return np.expm1(_ajustar_sarimax(y, ex, ordenes["SARIMAX"]).forecast(n, exog=ex_fut).values)
    m = _prophet(y, ex)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        return m.predict(_futuro(ex_fut)).yhat.values


def _semanal(idx: pd.DatetimeIndex, v: np.ndarray) -> pd.Series:
    s = pd.Series(v, idx)
    g = s.resample("W"); return g.sum()[g.count() == 7]


def metricas(y: pd.Series, f: np.ndarray) -> dict:
    a = y.values
    w, fw = _semanal(y.index, a), _semanal(y.index, f)
    return {"mape_diario": round(float(np.mean(np.abs((a - f) / a)) * 100), 2), "mape_semanal": round(float(np.mean(np.abs((w - fw) / w)) * 100), 2), "rmse_diario": round(float(np.sqrt(np.mean((a - f) ** 2))), 0), "mae_diario": round(float(np.mean(np.abs(a - f))), 0),
            "r2_diario": round(float(1 - ((a - f) ** 2).sum() / ((a - a.mean()) ** 2).sum()), 3), "error_total_pct": round(float((f.sum() - a.sum()) / a.sum() * 100), 2)}


def validar_origenes(s: pd.DataFrame, ex: pd.DataFrame, ordenes: dict) -> dict:
    """Vuelve a entrenar en cada origen y mide el error acumulado por horizonte."""
    fin = s.index[-1]; primero = fin - pd.Timedelta(days=DIAS_PRUEBA - 1)
    origenes = [primero + pd.Timedelta(days=PASO_ORIGENES * i) for i in range(4)]
    res = {}
    for m in MODELOS:
        filas = []
        for o in origenes:
            f = pronosticar(m, s.ventas[s.index < o], ex[ex.index < o], ex.loc[o:o + pd.Timedelta(days=max(HORIZONTES) - 1)], ordenes)
            a = s.ventas.loc[o:o + pd.Timedelta(days=max(HORIZONTES) - 1)].values
            filas.append({h: abs(f[:h].sum() - a[:h].sum()) / a[:h].sum() * 100 for h in HORIZONTES})
        res[m] = {str(h): round(float(np.mean([x[h] for x in filas])), 2) for h in HORIZONTES}
    return {"origenes": [str(o.date()) for o in origenes], "error_acumulado_medio_pct": res}


def descomposicion(s: pd.DataFrame) -> dict:
    y = s.ventas
    adf = adfuller(y, autolag="AIC"); adf_log = adfuller(np.log1p(y).diff(7).dropna(), autolag="AIC")
    st = STL(np.log1p(y), period=7, robust=True).fit()
    fuerza_est = 1 - st.resid.var() / (st.seasonal + st.resid).var(); fuerza_ten = 1 - st.resid.var() / (st.trend + st.resid).var()
    dia = y.groupby(y.index.day_of_week).mean()
    return {"adf_p_original": round(float(adf[1]), 4), "adf_p_log_dif7": float(f"{adf_log[1]:.2e}"), "fuerza_estacional_semanal": round(float(fuerza_est), 3), "fuerza_tendencia": round(float(fuerza_ten), 3),
            "indice_dia_semana": {d: round(float(v / dia.mean()), 3) for d, v in zip(["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"], dia.values)}, "efecto_quincena": round(float(y[s.quincena == 1].mean() / y[s.quincena == 0].mean()), 3)}


def pronostico_futuro(s: pd.DataFrame, ex: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """Entrena con toda la historia. El calendario de campañas futuro repite el de hace 52 semanas (supuesto)."""
    fechas = pd.date_range(s.index[-1] + pd.Timedelta(days=1), periods=max(HORIZONTES), freq="D")
    desc = pd.Series(s.descuento_campania.reindex(fechas - pd.Timedelta(days=364)).values, fechas)
    ex_f = calendario(fechas, desc)
    m = _prophet(s.ventas, ex, muestras=1000)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        fut = _futuro(ex_f); p = m.predict(fut); np.random.seed(SEED); muestras = m.predictive_samples(fut)["yhat"]
    tabla = pd.DataFrame({"fecha": fechas, "pronostico": p.yhat.round(2).values, "limite_inferior": p.yhat_lower.round(2).values, "limite_superior": p.yhat_upper.round(2).values, "descuento_campania_supuesto": desc.values})
    resumen = {str(h): {"pronostico": round(float(p.yhat.values[:h].sum()), 0), "limite_inferior_80": round(float(np.quantile(muestras[:h].sum(axis=0), .1)), 0), "limite_superior_80": round(float(np.quantile(muestras[:h].sum(axis=0), .9)), 0),
                        "mismo_periodo_anio_anterior": round(float(s.ventas.reindex(fechas[:h] - pd.Timedelta(days=364)).sum()), 0)} for h in HORIZONTES}
    return tabla, resumen


def analizar(s: pd.DataFrame) -> tuple[dict, pd.DataFrame]:
    ex = calendario(s.index, s.descuento_campania)
    corte = s.index[-1] - pd.Timedelta(days=DIAS_PRUEBA - 1)
    tr, te = s[s.index < corte], s[s.index >= corte]; xtr, xte = ex[ex.index < corte], ex[ex.index >= corte]
    ord_sarima, tabla_sarima = elegir_orden(tr.ventas, None); ord_sarimax, tabla_sarimax = elegir_orden(tr.ventas, xtr)
    ordenes = {"SARIMA": ord_sarima, "SARIMAX": ord_sarimax}
    hold, curvas = {}, {}
    for m in MODELOS:
        f = pronosticar(m, tr.ventas, xtr, xte, ordenes); hold[m] = metricas(te.ventas, f); curvas[m] = np.round(f, 0).tolist()
    pico_tr, pico_te = s[s.index < ORIGEN_TEMPORADA_ALTA], s.loc[ORIGEN_TEMPORADA_ALTA:ORIGEN_TEMPORADA_ALTA + pd.Timedelta(days=91)]
    pico = {m: metricas(pico_te.ventas, pronosticar(m, pico_tr.ventas, ex[ex.index < ORIGEN_TEMPORADA_ALTA], ex.loc[pico_te.index], ordenes)) for m in MODELOS}
    mejor = min(MODELOS, key=lambda m: hold[m]["mape_semanal"])
    tabla, futuro = pronostico_futuro(s, ex)
    return {
        "serie": {"dias": len(s), "inicio": str(s.index[0].date()), "fin": str(s.index[-1].date()), "ventas_total": round(float(s.ventas.sum()), 2), "dias_prueba": DIAS_PRUEBA, "inicio_prueba": str(corte.date())},
        "descomposicion": descomposicion(s), "ordenes": {"SARIMA": list(ord_sarima), "SARIMAX": list(ord_sarimax), "estacional": list(ORDEN_ESTACIONAL), "top_aic_sarima": tabla_sarima, "top_aic_sarimax": tabla_sarimax},
        "prueba_6_meses": hold, "mejor_modelo": mejor, "meta_mape_semanal": META_MAPE, "cumple_meta": bool(hold[mejor]["mape_semanal"] < META_MAPE),
        "validacion_por_horizonte": validar_origenes(s, ex, ordenes), "temporada_alta_2025": {"inicio": str(ORIGEN_TEMPORADA_ALTA.date()), "dias": len(pico_te), "metricas": pico},
        "curva_prueba": {"fechas": [str(d.date()) for d in te.index], "real": np.round(te.ventas.values, 0).tolist(), **{m: curvas[m] for m in MODELOS}},
        "pronostico_futuro": futuro, "supuesto_campanias": "El calendario futuro de campañas repite el de hace 52 semanas.",
    }, tabla


def main() -> dict:
    res, tabla = analizar(cargar())
    (REPORTS / "series.json").write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
    tabla.to_csv(REPORTS / "pronostico_ventas.csv", index=False)
    return res


if __name__ == "__main__":
    main()
