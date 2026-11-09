"""Segmentación de clientes y agrupación de productos.

Compara K-Means, clustering jerárquico y DBSCAN sobre RFM y LRFM.
Salidas: reports/clustering.json y data/processed/segmentos_clientes.csv.
Uso:  python -m src.models.clustering
"""
import json

import numpy as np
import pandas as pd
from sklearn.cluster import DBSCAN, AgglomerativeClustering, KMeans
from sklearn.decomposition import PCA
from sklearn.metrics import adjusted_rand_score, calinski_harabasz_score, davies_bouldin_score, silhouette_score
from sklearn.preprocessing import StandardScaler

from src.config import PROCESSED, REPORTS, SEED

RFM = ["recencia", "frecuencia", "monetario"]
LRFM = ["longitud", *RFM]
K_ELEGIDO = 3
K_RANGO = range(2, 9)
EPS_DBSCAN = [0.2, 0.25, 0.3, 0.35, 0.4, 0.5]
MIN_MUESTRAS = 20
MUESTRA_SILUETA = 5000
META_SILUETA = 0.4


def matriz(df: pd.DataFrame, columnas: list[str]) -> np.ndarray:
    """Logaritmo para reducir la asimetría y estandarización para igualar escalas."""
    return StandardScaler().fit_transform(np.log1p(df[columnas]))


def _silueta(x, etiquetas) -> float:
    return round(float(silhouette_score(x, etiquetas, sample_size=min(MUESTRA_SILUETA, len(x)), random_state=SEED)), 3)


def _metricas(x, etiquetas) -> dict:
    return {"silhouette": _silueta(x, etiquetas), "davies_bouldin": round(float(davies_bouldin_score(x, etiquetas)), 3), "calinski_harabasz": round(float(calinski_harabasz_score(x, etiquetas)), 1)}


def _kmeans(k: int, semilla: int = SEED) -> KMeans:
    return KMeans(k, n_init=10, random_state=semilla)


def barrido_k(x: np.ndarray) -> list[dict]:
    r = []
    for k in K_RANGO:
        m = _kmeans(k).fit(x)
        r.append({"k": k, "inercia": round(float(m.inertia_), 1), **_metricas(x, m.labels_)})
    return r


def estabilidad(x: np.ndarray, k: int, repeticiones: int = 20) -> dict:
    """Concordancia (ARI) con la solución base al cambiar la semilla y al usar 80 % de los clientes."""
    base = _kmeans(k).fit(x)
    rng = np.random.default_rng(SEED)
    semillas, muestras = [], []
    for i in range(repeticiones):
        semillas.append(adjusted_rand_score(base.labels_, _kmeans(k, SEED + i + 1).fit_predict(x)))
        idx = rng.choice(len(x), int(.8 * len(x)), replace=False)
        muestras.append(adjusted_rand_score(base.labels_[idx], _kmeans(k, SEED + i + 1).fit(x[idx]).labels_))
    return {"ari_medio_semillas": round(float(np.mean(semillas)), 3), "ari_medio_submuestras": round(float(np.mean(muestras)), 3), "ari_min_submuestras": round(float(np.min(muestras)), 3)}


def barrido_dbscan(x: np.ndarray) -> list[dict]:
    r = []
    for eps in EPS_DBSCAN:
        e = DBSCAN(eps=eps, min_samples=MIN_MUESTRAS).fit_predict(x)
        k, ruido = len(set(e)) - int(-1 in e), float((e == -1).mean())
        r.append({"eps": eps, "grupos": k, "ruido_pct": round(100 * ruido, 1), "silhouette": _silueta(x[e != -1], e[e != -1]) if k > 1 else None})
    return r


def _nombrar(perfil: pd.DataFrame) -> dict[int, str]:
    """Nombra por comportamiento, no por número: el mismo criterio sirve si cambia el orden de los grupos."""
    activos = perfil.recencia.idxmin()
    resto = perfil.drop(index=activos)
    return {activos: "Alto valor activos", resto.monetario.idxmax(): "Valiosos inactivos", resto.monetario.idxmin(): "Ocasionales inactivos"}


def perfilar(v: pd.DataFrame, etiquetas: np.ndarray) -> tuple[pd.DataFrame, pd.Series]:
    d = v.assign(grupo=etiquetas)
    p = d.groupby("grupo").agg(clientes=("cliente_id", "size"), recencia=("recencia", "median"), frecuencia=("frecuencia", "median"), monetario=("monetario", "median"), longitud=("longitud", "median"),
                               ticket_medio=("ticket_medio", "median"), clv=("clv", "median"), rfm_total=("rfm_total", "mean"), ventas=("monetario", "sum"), clv_total=("clv", "sum"), pct_retraso=("pct_retraso", "mean"),
                               devoluciones=("devoluciones", "mean"), tickets=("tickets", "mean"), tasa_clic=("tasa_clic", "mean"), n_subcategorias=("n_subcategorias", "mean"), edad=("edad", "mean"), activos_180d=("recencia", lambda s: float((s <= 180).mean())))
    p["pct_clientes"] = 100 * p.clientes / p.clientes.sum(); p["pct_ventas"] = 100 * p.ventas / p.ventas.sum(); p["activos_180d"] *= 100
    nombres = _nombrar(p)
    return p.rename(index=nombres).sort_values("recencia"), pd.Series(etiquetas).map(nombres)


def variables_producto(productos: pd.DataFrame, items: pd.DataFrame, devol: pd.DataFrame) -> pd.DataFrame:
    v = items[items.pedido_valido]
    g = v.groupby("producto_id").agg(pedidos=("pedido_id", "nunique"), descuento_medio=("descuento", "mean"))
    p = productos.set_index("producto_id").join(g)
    p["margen_pct"] = 100 * (1 - p.costo / p.precio_lista)
    p["tasa_devolucion"] = (devol.groupby("producto_id").size().reindex(p.index).fillna(0) / v.groupby("producto_id").size().reindex(p.index)).fillna(0)
    return p.dropna(subset=["pedidos"]).reset_index()


def agrupar_productos(p: pd.DataFrame) -> dict:
    cols = ["ingresos", "unidades", "cv_unidades", "precio_lista", "margen_pct", "tasa_devolucion", "descuento_medio"]
    a = p[cols].copy(); a[["ingresos", "unidades", "cv_unidades", "precio_lista"]] = np.log1p(a[["ingresos", "unidades", "cv_unidades", "precio_lista"]])
    x = StandardScaler().fit_transform(a)
    barrido = [{"k": k, **_metricas(x, _kmeans(k).fit_predict(x))} for k in range(2, 8)]
    k = max(barrido, key=lambda r: r["silhouette"])["k"]
    e = _kmeans(k).fit_predict(x)
    d = p.assign(grupo=e)
    perfil = d.groupby("grupo").agg(productos=("producto_id", "size"), ingresos=("ingresos", "median"), unidades=("unidades", "median"), precio=("precio_lista", "median"), cv=("cv_unidades", "median"), devolucion_pct=("tasa_devolucion", lambda s: 100 * s.mean()), ingresos_total=("ingresos", "sum"))
    perfil["pct_ingresos"] = 100 * perfil.ingresos_total / perfil.ingresos_total.sum()
    cruce = {str(g): {str(c): int(n) for c, n in d[d.grupo == g].categoria.value_counts().items()} for g in sorted(set(e))}
    return {"barrido": barrido, "k": k, "silhouette": _metricas(x, e), "perfil": perfil.round(2).reset_index().to_dict("records"), "categorias": cruce, "abc_por_grupo": pd.crosstab(d.grupo, d["abc"]).to_dict("index")}


def analizar(v: pd.DataFrame, productos: pd.DataFrame, items: pd.DataFrame, devol: pd.DataFrame) -> tuple[dict, pd.DataFrame]:
    x_rfm, x_lrfm = matriz(v, RFM), matriz(v, LRFM)
    km = _kmeans(K_ELEGIDO).fit(x_rfm)
    jer = AgglomerativeClustering(K_ELEGIDO, linkage="ward").fit_predict(x_rfm)
    barrido_d = barrido_dbscan(x_rfm)
    ops = [r for r in barrido_d if r["silhouette"] is not None and r["ruido_pct"] <= 10] or [r for r in barrido_d if r["silhouette"] is not None]
    mejor = max(ops, key=lambda r: r["silhouette"])
    db = DBSCAN(eps=mejor["eps"], min_samples=MIN_MUESTRAS).fit_predict(x_rfm)
    perfil, nombre = perfilar(v, km.labels_)
    seg = v[["cliente_id", *LRFM, "ticket_medio", "clv", "rfm_total", "lrfm_total"]].assign(segmento=nombre.values, atipico_dbscan=(db == -1))
    pca = PCA(2, random_state=SEED).fit(x_rfm); xy = pca.transform(x_rfm)
    atip = v[db == -1]; norm = v[db != -1]
    rng = np.random.default_rng(SEED); idx = rng.choice(len(v), min(2500, len(v)), replace=False)
    res = {
        "clientes": len(v),
        "barrido_rfm": barrido_k(x_rfm), "barrido_lrfm": barrido_k(x_lrfm),
        "comparacion": {"K-Means RFM (k=3)": {**_metricas(x_rfm, km.labels_), "grupos": K_ELEGIDO, "ruido_pct": 0.0}, "K-Means LRFM (k=3)": {**_metricas(x_lrfm, _kmeans(K_ELEGIDO).fit_predict(x_lrfm)), "grupos": K_ELEGIDO, "ruido_pct": 0.0},
                        "Jerárquico Ward RFM (k=3)": {**_metricas(x_rfm, jer), "grupos": K_ELEGIDO, "ruido_pct": 0.0}, f"DBSCAN RFM (eps={mejor['eps']})": {**_metricas(x_rfm[db != -1], db[db != -1]), "grupos": mejor["grupos"], "ruido_pct": mejor["ruido_pct"]}},
        "concordancia_kmeans_jerarquico_ari": round(float(adjusted_rand_score(km.labels_, jer)), 3),
        "barrido_dbscan": barrido_d, "estabilidad_k3": estabilidad(x_rfm, K_ELEGIDO), "meta_silhouette": META_SILUETA,
        "perfil_segmentos": perfil.round(2).reset_index(names="segmento").to_dict("records"),
        "atipicos_dbscan": {"clientes": int((db == -1).sum()), "monetario_mediana": round(float(atip.monetario.median()), 2), "monetario_mediana_resto": round(float(norm.monetario.median()), 2), "frecuencia_mediana": float(atip.frecuencia.median()), "frecuencia_mediana_resto": float(norm.frecuencia.median()), "pct_ventas": round(100 * float(atip.monetario.sum() / v.monetario.sum()), 1)},
        "pca": {"varianza_2d_pct": round(100 * float(pca.explained_variance_ratio_.sum()), 1), "x": np.round(xy[idx, 0], 3).tolist(), "y": np.round(xy[idx, 1], 3).tolist(), "segmento": nombre.values[idx].tolist()},
        "productos": agrupar_productos(variables_producto(productos, items, devol)),
    }
    return res, seg


def main() -> dict:
    leer = lambda n, **k: pd.read_csv(PROCESSED / f"{n}.csv", **k)
    res, seg = analizar(leer("clientes_variables"), leer("productos_abc_xyz"), leer("ventas_items", usecols=["pedido_id", "producto_id", "descuento", "pedido_valido"]), leer("devoluciones"))
    (REPORTS / "clustering.json").write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
    seg.to_csv(PROCESSED / "segmentos_clientes.csv", index=False)
    return res


if __name__ == "__main__":
    main()
