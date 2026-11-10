"""Regresión de ventas por producto y mes, y del valor futuro del cliente.

Salidas: reports/regresion.json y reports/predicciones_regresion.csv.
Uso:  python -m src.models.regresion
"""
import json
import warnings

import numpy as np
import pandas as pd
from sklearn.base import clone
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor
from sklearn.impute import SimpleImputer
from sklearn.inspection import permutation_importance
from sklearn.linear_model import ElasticNet, Lasso, LinearRegression, Ridge
from sklearn.metrics import mean_absolute_error, r2_score, root_mean_squared_error
from sklearn.model_selection import GridSearchCV, KFold, cross_validate
from sklearn.pipeline import Pipeline, make_pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from xgboost import XGBRegressor

from src.config import PROCESSED, REPORTS, SEED
from src.features.variables import cargar_procesados, variables_cliente

INICIO_PRUEBA = "2026-04"
INICIO_ENTRENAMIENTO = "2024-01"  # el primer mes con rezago de 12 meses
META_R2 = 0.6
CORTE_CLV = pd.Timestamp("2025-10-01")
FIN_CLV = pd.Timestamp("2026-10-01")
BLOQUES = {"Historial de ventas": ["ventas_lag1", "ventas_lag2", "ventas_lag3", "ventas_lag12", "ventas_media_3m", "ventas_media_historica"], "Precio y costo": ["precio_lista", "costo"], "Campañas": ["descuento_max", "dias_campania"],
           "Inventario": ["stock_inicial", "quiebre_lag1"], "Compradores": ["compradores_lag1"], "Calendario": ["periodo", "mes_del_anio"], "Producto": ["categoria", "marca"]}
NUMERICAS = [c for b, cols in BLOQUES.items() if b != "Producto" for c in cols]
CATEGORICAS = BLOQUES["Producto"]
VARIABLES = NUMERICAS + CATEGORICAS


def preparador(numericas: list[str], categoricas: list[str], escalar: bool = True) -> ColumnTransformer:
    pasos = [SimpleImputer(strategy="median")] + ([StandardScaler()] if escalar else [])
    return ColumnTransformer([("num", make_pipeline(*pasos), numericas), ("cat", OneHotEncoder(handle_unknown="ignore", sparse_output=False), categoricas)])


def catalogo() -> dict:
    """(modelo, escalar, rejilla). Los árboles no necesitan escalamiento."""
    return {"Regresión múltiple": (LinearRegression(), True, {}),
            "Ridge": (Ridge(), True, {"m__alpha": [1, 10, 100, 1000]}), "Lasso": (Lasso(max_iter=20000), True, {"m__alpha": [.1, 1, 10]}),
            "Elastic Net": (ElasticNet(max_iter=20000), True, {"m__alpha": [.1, 1], "m__l1_ratio": [.2, .8]}),
            "Random Forest": (RandomForestRegressor(200, random_state=SEED, n_jobs=1), False, {"m__min_samples_leaf": [2, 5, 10], "m__max_depth": [8, 14]}),
            "Gradient Boosting": (GradientBoostingRegressor(random_state=SEED, n_estimators=200), False, {"m__learning_rate": [.03, .08], "m__max_depth": [2, 3]}),
            "XGBoost": (XGBRegressor(n_estimators=300, random_state=SEED, n_jobs=1, verbosity=0), False, {"m__learning_rate": [.03, .08], "m__max_depth": [2, 3]})}


def pliegues_temporales(meses: pd.Series, n: int = 3, largo: int = 3) -> list:
    """Bloques consecutivos al final del entrenamiento: siempre se valida con meses posteriores."""
    orden = sorted(meses.unique()); r = []
    for i in range(n, 0, -1):
        ini, fin = orden[-i * largo], orden[-(i - 1) * largo] if i > 1 else None
        val = (meses >= ini) & ((meses < fin) if fin else True)
        r.append((np.flatnonzero(meses < ini), np.flatnonzero(val)))
    return r


def metricas(y, p) -> dict:
    y, p = np.asarray(y, float), np.asarray(p, float)
    return {"r2": round(float(r2_score(y, p)), 3), "rmse": round(float(root_mean_squared_error(y, p)), 1), "mae": round(float(mean_absolute_error(y, p)), 1), "wape_pct": round(float(np.abs(y - p).sum() / y.sum() * 100), 1)}


def _permutacion(m: Pipeline, x: pd.DataFrame, y: pd.Series) -> pd.Series:
    r = permutation_importance(m, x, y, n_repeats=10, random_state=SEED, scoring="r2", n_jobs=-1)
    return pd.Series(r.importances_mean, x.columns).sort_values(ascending=False)


def importancia_bloques(m: Pipeline, x: pd.DataFrame, y: pd.Series) -> dict:
    """Caída de R² al barajar juntas las variables de un bloque, para no repartir su efecto entre variables parecidas."""
    rng = np.random.default_rng(SEED); base = r2_score(y, m.predict(x)); r = {}
    for b, cols in BLOQUES.items():
        caidas = []
        for _ in range(10):
            a = x.copy(); idx = rng.permutation(len(a)); a[cols] = x[cols].values[idx]
            caidas.append(base - r2_score(y, m.predict(a)))
        r[b] = round(float(np.mean(caidas)), 3)
    return dict(sorted(r.items(), key=lambda kv: -kv[1]))


def ventas(p: pd.DataFrame) -> tuple[dict, pd.DataFrame]:
    d = p[p.mes >= INICIO_ENTRENAMIENTO].copy(); tr, te = d[d.mes < INICIO_PRUEBA].reset_index(drop=True), d[d.mes >= INICIO_PRUEBA].reset_index(drop=True)
    cv = pliegues_temporales(tr.mes)
    res = {"Referencia (promedio móvil 3 meses)": {**metricas(te.ventas, te.ventas_media_3m), "parametros": {}}}
    simple = make_pipeline(SimpleImputer(strategy="median"), LinearRegression()).fit(tr[["ventas_media_3m"]], tr.ventas)
    res["Regresión lineal simple"] = {**metricas(te.ventas, simple.predict(te[["ventas_media_3m"]])), "parametros": {}}
    ajustados = {}
    for n, (est, esc, rej) in catalogo().items():
        pipe = Pipeline([("pre", preparador(NUMERICAS, CATEGORICAS, esc)), ("m", clone(est))])
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            g = GridSearchCV(pipe, rej or {"m__fit_intercept": [True]}, cv=cv, scoring="r2", n_jobs=-1, refit=True).fit(tr[VARIABLES], tr.ventas)
        ajustados[n] = g.best_estimator_
        res[n] = {**metricas(te.ventas, g.predict(te[VARIABLES])), "r2_validacion": round(float(g.best_score_), 3), "parametros": {k.replace("m__", ""): v for k, v in g.best_params_.items() if k != "m__fit_intercept"}}
    candidatos = [k for k in ajustados]
    mejor = max(candidatos, key=lambda k: res[k]["r2_validacion"])  # se elige en validación, no en la prueba
    m = ajustados[mejor]; pred = np.clip(m.predict(te[VARIABLES]), 0, None)
    t = te.assign(prediccion=pred)
    tot = t.groupby("mes").agg(real=("ventas", "sum"), prediccion=("prediccion", "sum")); cat = t.groupby("categoria").apply(lambda g: pd.Series(metricas(g.ventas, g.prediccion)), include_groups=False)
    imp = _permutacion(m, te[VARIABLES], te.ventas)
    ridge = ajustados["Ridge"]; nombres = ridge.named_steps["pre"].get_feature_names_out(); coefs = pd.Series(ridge.named_steps["m"].coef_, [n.split("__")[1] for n in nombres])
    return {"filas_entrenamiento": len(tr), "filas_prueba": len(te), "meses_prueba": sorted(te.mes.unique().tolist()), "modelos": res, "mejor_modelo": mejor, "meta_r2": META_R2, "cumple_meta": bool(res[mejor]["r2"] > META_R2),
            "total_mensual": {"mes": tot.index.tolist(), "real": tot.real.round(0).tolist(), "prediccion": tot.prediccion.round(0).tolist(), "wape_pct": round(float((tot.real - tot.prediccion).abs().sum() / tot.real.sum() * 100), 1)},
            "por_categoria": cat.round(3).to_dict("index"), "importancia_variables": imp.round(4).to_dict(), "importancia_bloques": importancia_bloques(m, te[VARIABLES], te.ventas),
            "coeficientes_ridge": coefs[[c for c in NUMERICAS]].sort_values(key=np.abs, ascending=False).round(1).to_dict()}, t[["producto_id", "mes", "categoria", "subcategoria", "ventas", "prediccion"]].round(2)


def efecto_visitas(p: pd.DataFrame) -> dict:
    """Las sesiones solo existen desde 2025: se compara el mismo modelo con y sin ellas en ese tramo."""
    d = p.dropna(subset=["sesiones_lag1"]); tr, te = d[d.mes < INICIO_PRUEBA], d[d.mes >= INICIO_PRUEBA]
    def probar(num):
        m = Pipeline([("pre", preparador(num, CATEGORICAS)), ("m", Ridge(alpha=100))]).fit(tr[num + CATEGORICAS], tr.ventas)
        return metricas(te.ventas, m.predict(te[num + CATEGORICAS]))
    return {"filas_entrenamiento": len(tr), "meses_entrenamiento": int(tr.mes.nunique()), "sin_sesiones": probar(NUMERICAS), "con_sesiones": probar(NUMERICAS + ["sesiones_lag1"])}


def valor_cliente(t: dict[str, pd.DataFrame]) -> dict:
    """Análisis secundario: gasto de los 12 meses siguientes a partir de lo ocurrido antes del corte."""
    x = variables_cliente(t, CORTE_CLV)
    ped = t["pedidos_integrados"]; ped = ped[ped.pedido_valido & (ped.fecha_pedido >= CORTE_CLV) & (ped.fecha_pedido < FIN_CLV)]
    y = x.cliente_id.map(ped.groupby("cliente_id").monto_total.sum()).fillna(0.0)
    cat = ["genero", "zona", "canal_adquisicion", "deporte_preferido"]; num = [c for c in x.columns if c not in cat + ["cliente_id", "departamento", "edad_faltante"]]
    cv = KFold(5, shuffle=True, random_state=SEED)  # los clientes de gasto muy alto hacen inestable una sola partición
    ref = [r2_score(y.iloc[b], x.monetario_365d.iloc[b]) for _, b in cv.split(x)]
    res = {"Referencia (gasto de los 12 meses previos)": {"r2_medio": round(float(np.mean(ref)), 3), "r2_desv": round(float(np.std(ref)), 3), "mae_medio": round(float((y - x.monetario_365d).abs().mean()), 1)}}
    for n, (est, esc) in {"Ridge": (Ridge(alpha=100), True), "Random Forest": (RandomForestRegressor(300, min_samples_leaf=5, random_state=SEED, n_jobs=-1), False), "XGBoost": (XGBRegressor(n_estimators=300, max_depth=3, learning_rate=.05, random_state=SEED, verbosity=0), False)}.items():
        c = cross_validate(Pipeline([("pre", preparador(num, cat, esc)), ("m", est)]), x[num + cat], y, cv=cv, scoring={"r2": "r2", "mae": "neg_mean_absolute_error"})
        res[n] = {"r2_medio": round(float(c["test_r2"].mean()), 3), "r2_desv": round(float(c["test_r2"].std()), 3), "r2_min": round(float(c["test_r2"].min()), 3), "r2_max": round(float(c["test_r2"].max()), 3), "mae_medio": round(float(-c["test_mae"].mean()), 1)}
    return {"compradores": len(x), "pct_gasto_futuro_cero": round(100 * float((y == 0).mean()), 1), "gasto_p50": round(float(y.median()), 2), "gasto_p99": round(float(y.quantile(.99)), 2), "modelos": res, "meta_r2": META_R2}


def main() -> dict:
    p = pd.read_csv(PROCESSED / "panel_producto_mes.csv")
    v, pred = ventas(p)
    res = {"ventas": v, "visitas": efecto_visitas(p), "valor_cliente": valor_cliente(cargar_procesados())}
    (REPORTS / "regresion.json").write_text(json.dumps(res, ensure_ascii=False, indent=1, default=float), encoding="utf-8")
    pred.to_csv(REPORTS / "predicciones_regresion.csv", index=False)
    return res


if __name__ == "__main__":
    main()
