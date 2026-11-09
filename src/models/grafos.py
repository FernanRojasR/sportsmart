"""Minería de grafos: relaciones entre clientes, productos y categorías.

Salidas: reports/grafos.json y reports/grafo_productos.csv.
Uso:  python -m src.models.grafos
"""
import itertools
import json

import networkx as nx
import numpy as np
import pandas as pd
from sklearn.metrics import adjusted_rand_score
from sklearn.neighbors import NearestNeighbors

from src.config import PROCESSED, REPORTS, SEED

COOCURRENCIA_MIN = 5
META_MODULARIDAD = 0.3
ESTRELLAS_RECOMIENDA = 4
REPETICIONES_AZAR = 10
SEMILLAS_LOUVAIN = 20


def coocurrencias(items: pd.DataFrame, columna: str) -> pd.Series:
    """Número de pedidos en que coincide cada par."""
    p = items[["pedido_id", columna]].drop_duplicates()
    m = p.merge(p, on="pedido_id", suffixes=("_a", "_b"))
    m = m[m[f"{columna}_a"] < m[f"{columna}_b"]]
    return m.groupby([f"{columna}_a", f"{columna}_b"]).size().rename("pedidos")


def grafo(w: pd.Series) -> nx.Graph:
    g = nx.Graph()
    g.add_weighted_edges_from((a, b, int(v)) for (a, b), v in w.items())
    return g


def comunidades(g: nx.Graph, semilla: int = SEED) -> list[set]:
    return sorted(nx.community.louvain_communities(g, weight="weight", seed=semilla), key=len, reverse=True)


def modularidad(g: nx.Graph, c: list[set]) -> float:
    return float(nx.community.modularity(g, c, weight="weight"))


def _vector(nodos: list, c: list[set]) -> list[int]:
    d = {n: i for i, s in enumerate(c) for n in s}
    return [d[n] for n in nodos]


def estabilidad(g: nx.Graph, base: list[set]) -> dict:
    nodos = list(g.nodes); vb = _vector(nodos, base); mods, aris = [], []
    for i in range(SEMILLAS_LOUVAIN):
        c = comunidades(g, SEED + i + 1); mods.append(modularidad(g, c)); aris.append(adjusted_rand_score(vb, _vector(nodos, c)))
    return {"modularidad_media": round(float(np.mean(mods)), 3), "modularidad_min": round(float(np.min(mods)), 3), "ari_medio": round(float(np.mean(aris)), 3)}


def referencia_azar(items: pd.DataFrame) -> dict:
    """Baraja los productos entre las líneas: conserva el tamaño de las canastas y la popularidad."""
    rng = np.random.default_rng(SEED); mods = []
    for _ in range(REPETICIONES_AZAR):
        a = items[["pedido_id"]].assign(producto_id=rng.permutation(items.producto_id.values))
        w = coocurrencias(a, "producto_id"); g = grafo(w[w >= COOCURRENCIA_MIN])
        mods.append(modularidad(g, comunidades(g)))
    return {"modularidad_media": round(float(np.mean(mods)), 3), "modularidad_max": round(float(np.max(mods)), 3), "repeticiones": len(mods)}


def centralidades(g: nx.Graph) -> pd.DataFrame:
    for _, _, d in g.edges(data=True):
        d["distancia"] = 1 / d["weight"]
    return pd.DataFrame({"grado": dict(g.degree()), "fuerza": dict(g.degree(weight="weight")), "pagerank": nx.pagerank(g, weight="weight"), "intermediacion": nx.betweenness_centrality(g, weight="distancia")}).rename_axis("producto_id").reset_index()


def relaciones_categoria(items: pd.DataFrame, columna: str) -> pd.DataFrame:
    """Lift entre pares: cuántas veces más coinciden que si fueran independientes."""
    c = pd.crosstab(items.pedido_id, items[columna]).astype(bool)
    n = len(c); a = c.to_numpy(dtype=float); conj = a.T @ a / n; p = a.mean(axis=0)
    return pd.DataFrame(conj / np.outer(p, p), index=c.columns, columns=c.columns)


def patrones_frecuentes(items: pd.DataFrame, top: int = 8) -> list[dict]:
    """Tríadas de subcategorías más frecuentes frente a lo esperado por azar."""
    c = pd.crosstab(items.pedido_id, items.subcategoria).astype(bool); n = len(c); r = []
    for a, b, d in itertools.combinations(c.columns, 3):
        k = int((c[a] & c[b] & c[d]).sum())
        if k:
            r.append({"patron": f"{a} + {b} + {d}", "pedidos": k, "soporte_pct": round(100 * k / n, 3), "veces_sobre_azar": round(k / n / (c[a].mean() * c[b].mean() * c[d].mean()), 1)})
    return sorted(r, key=lambda x: -x["pedidos"])[:top]


def relacion_recomienda(items: pd.DataFrame, opiniones: pd.DataFrame) -> pd.DataFrame:
    """Reseñas de pedidos con un solo producto, para saber a qué producto se refiere la opinión."""
    uno = items.groupby("pedido_id").producto_id.agg(["nunique", "first"]); uno = uno[uno["nunique"] == 1]["first"].rename("producto_id")
    o = opiniones.dropna(subset=["puntuacion"]).merge(uno, left_on="pedido_id", right_index=True)
    return o.assign(recomienda=o.puntuacion >= ESTRELLAS_RECOMIENDA)[["cliente_id", "producto_id", "puntuacion", "recomienda"]]


def grafo_heterogeneo(items: pd.DataFrame, rec: pd.DataFrame) -> nx.MultiGraph:
    g = nx.MultiGraph()
    compras = items.groupby(["cliente_id", "producto_id"]).size()
    g.add_nodes_from(items.cliente_id.unique(), tipo="cliente"); g.add_nodes_from(items.producto_id.unique(), tipo="producto")
    g.add_edges_from((c, p, {"tipo": "compra", "veces": int(v)}) for (c, p), v in compras.items())
    g.add_edges_from((c, p, {"tipo": "recomienda"}) for c, p in zip(rec[rec.recomienda].cliente_id, rec[rec.recomienda].producto_id))
    return g


def clientes_relacionados(items: pd.DataFrame, clientes: pd.DataFrame, com: dict) -> dict:
    """Afinidad con cada comunidad y vecinos más parecidos según lo que compran."""
    i = items.assign(comunidad=items.producto_id.map(com)).dropna(subset=["comunidad"])
    t = pd.crosstab(i.cliente_id, i.comunidad); t = t[t.sum(axis=1) >= 3]
    share = t.div(t.sum(axis=1), axis=0); principal = share.idxmax(axis=1)
    dep = clientes.set_index("cliente_id").deporte_preferido.reindex(t.index)
    cruce = pd.crosstab(principal.astype(int), dep, normalize="index").round(3)
    m = pd.crosstab(items.cliente_id, items.subcategoria); m = m[m.sum(axis=1) >= 3]; d = clientes.set_index("cliente_id").deporte_preferido.reindex(m.index)
    nn = NearestNeighbors(n_neighbors=2, metric="cosine").fit(m.values); dist, idx = nn.kneighbors(m.values)
    es_propio = idx[:, 0] == np.arange(len(m))  # con empates, el propio cliente puede no salir primero
    vecino, distancia = np.where(es_propio, idx[:, 1], idx[:, 0]), np.where(es_propio, dist[:, 1], dist[:, 0])
    base = float((d.value_counts(normalize=True) ** 2).sum())
    return {"clientes_con_3_o_mas_items": int(len(t)), "pct_concentrado_60": round(100 * float((share.max(axis=1) >= .6).mean()), 1), "pct_por_comunidad": {str(int(k)): round(100 * float(v), 1) for k, v in principal.value_counts(normalize=True).sort_index().items()},
            "deporte_por_comunidad": {str(int(a)): {c: float(v) for c, v in fila.items()} for a, fila in cruce.iterrows()},
            "vecino_comparte_deporte_pct": round(100 * float((d.values == d.values[vecino]).mean()), 1), "azar_comparte_deporte_pct": round(100 * base, 1), "similitud_coseno_media_vecino": round(float(1 - distancia.mean()), 3)}


def analizar(items: pd.DataFrame, opiniones: pd.DataFrame, clientes: pd.DataFrame) -> tuple[dict, pd.DataFrame]:
    v = items[items.pedido_valido].copy()
    w = coocurrencias(v, "producto_id"); g = grafo(w[w >= COOCURRENCIA_MIN]); g_todo = grafo(w)
    com = comunidades(g); mod = modularidad(g, com)
    rec = relacion_recomienda(v, opiniones); het = grafo_heterogeneo(v, rec)
    tipo = pd.Series([d["tipo"] for *_, d in het.edges(data=True)]).value_counts()
    nodo_com = {n: i for i, s in enumerate(com) for n in s}
    info = v.drop_duplicates("producto_id").set_index("producto_id")[["categoria", "subcategoria"]]
    nodos = centralidades(g).assign(comunidad=lambda d: d.producto_id.map(nodo_com)).join(info, on="producto_id").sort_values("pagerank", ascending=False)
    ing = v.groupby("producto_id").importe.sum()
    perfil = []
    for i, s in enumerate(com):
        sub = info.loc[list(s)].subcategoria.value_counts()
        perfil.append({"comunidad": i, "productos": len(s), "subcategorias_principales": list(sub.index[:5]), "categorias": info.loc[list(s)].categoria.value_counts().to_dict(), "ingresos_pct": round(100 * float(ing.reindex(list(s)).sum() / ing.sum()), 1), "etiqueta": " · ".join(sub.index[:3])})
    sub_com = nodos.groupby("subcategoria").comunidad.agg(lambda x: int(x.value_counts().idxmax())).to_dict()
    lift_sub = relaciones_categoria(v, "subcategoria"); lift_cat = relaciones_categoria(v, "categoria")
    tmp = rec.groupby("producto_id").agg(resenas=("recomienda", "size"), recomendaciones=("recomienda", "sum")).assign(pct=lambda d: 100 * d.recomendaciones / d.resenas).join(info)
    top_rec = tmp[tmp.resenas >= 10].sort_values(["pct", "recomendaciones"], ascending=False).head(8).round(1).reset_index().to_dict("records")
    sim = lift_sub.where(np.triu(np.ones(lift_sub.shape, dtype=bool), 1)).stack().sort_values(ascending=False)
    res = {
        "heterogeneo": {"clientes": sum(1 for _, d in het.nodes(data=True) if d["tipo"] == "cliente"), "productos": sum(1 for _, d in het.nodes(data=True) if d["tipo"] == "producto"), "aristas_compra": int(tipo.get("compra", 0)), "aristas_recomienda": int(tipo.get("recomienda", 0)), "resenas_un_producto": len(rec), "pct_recomienda": round(100 * float(rec.recomienda.mean()), 1)},
        "producto_producto": {"umbral_pedidos": COOCURRENCIA_MIN, "nodos": g.number_of_nodes(), "aristas": g.number_of_edges(), "densidad": round(nx.density(g), 4), "componentes": nx.number_connected_components(g), "coef_agrupamiento": round(nx.average_clustering(g), 3), "modularidad_sin_umbral": round(modularidad(g_todo, comunidades(g_todo)), 3)},
        "comunidades": {"n": len(com), "modularidad": round(mod, 3), "meta": META_MODULARIDAD, "cumple_meta": bool(mod > META_MODULARIDAD), "estabilidad": estabilidad(g, com), "referencia_azar": referencia_azar(v), "perfil": perfil},
        "productos_centrales": nodos.head(10).round(4).to_dict("records"),
        "recomendaciones_top": top_rec,
        "categorias": {"lift": lift_cat.round(2).to_dict()},
        "subcategorias": {"comunidad": sub_com, "top_pares_lift": [{"a": a, "b": b, "lift": round(float(l), 2)} for (a, b), l in sim.head(10).items()], "lift": lift_sub.round(2).to_dict()},
        "patrones_frecuentes": patrones_frecuentes(v),
        "clientes_relacionados": clientes_relacionados(v, clientes, nodo_com),
    }
    return res, nodos


def main() -> dict:
    items = pd.read_csv(PROCESSED / "ventas_items.csv", usecols=["pedido_id", "cliente_id", "producto_id", "categoria", "subcategoria", "importe", "pedido_valido"])
    res, nodos = analizar(items, pd.read_csv(PROCESSED / "opiniones.csv"), pd.read_csv(PROCESSED / "clientes.csv"))
    (REPORTS / "grafos.json").write_text(json.dumps(res, ensure_ascii=False, indent=1, default=float), encoding="utf-8")
    nodos.to_csv(REPORTS / "grafo_productos.csv", index=False)
    return res


if __name__ == "__main__":
    main()
