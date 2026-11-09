"""Pruebas de minería de grafos. Ejecutar: pytest -q"""
import networkx as nx
import pandas as pd
import pytest

from src.features.preparacion import cargar_crudos, integrar, preparar
from src.models.grafos import COOCURRENCIA_MIN, META_MODULARIDAD, comunidades, coocurrencias, grafo, grafo_heterogeneo, modularidad, relacion_recomienda, relaciones_categoria


def test_coocurrencias_cuentan_pedidos():
    items = pd.DataFrame({"pedido_id": [1, 1, 2, 2, 3], "producto_id": ["a", "b", "a", "b", "a"]})
    assert coocurrencias(items, "producto_id").to_dict() == {("a", "b"): 2}


def test_dos_grupos_separados_tienen_alta_modularidad():
    w = pd.Series({("a", "b"): 10, ("b", "c"): 10, ("a", "c"): 10, ("x", "y"): 10, ("y", "z"): 10, ("x", "z"): 10, ("c", "x"): 1})
    g = grafo(w); c = comunidades(g)
    assert len(c) == 2 and modularidad(g, c) > META_MODULARIDAD


def test_recomienda_solo_usa_pedidos_de_un_producto():
    items = pd.DataFrame({"pedido_id": [1, 2, 2], "producto_id": ["a", "b", "c"]})
    opi = pd.DataFrame({"pedido_id": [1, 2], "cliente_id": ["u", "v"], "puntuacion": [5.0, 5.0]})
    r = relacion_recomienda(items, opi)
    assert r.producto_id.tolist() == ["a"] and r.recomienda.tolist() == [True]


def test_tres_estrellas_no_recomienda():
    items = pd.DataFrame({"pedido_id": [1], "producto_id": ["a"]})
    assert not relacion_recomienda(items, pd.DataFrame({"pedido_id": [1], "cliente_id": ["u"], "puntuacion": [3.0]})).recomienda.iloc[0]


def test_grafo_tiene_compra_y_recomienda():
    items = pd.DataFrame({"pedido_id": [1, 2], "cliente_id": ["u", "u"], "producto_id": ["a", "a"]})
    g = grafo_heterogeneo(items, pd.DataFrame({"cliente_id": ["u"], "producto_id": ["a"], "recomienda": [True]}))
    assert isinstance(g, nx.MultiGraph) and sorted(d["tipo"] for *_, d in g.edges(data=True)) == ["compra", "recomienda"]
    assert g.nodes["u"]["tipo"] == "cliente"


def test_lift_conocido():
    items = pd.DataFrame({"pedido_id": [1, 1, 2, 3, 4], "categoria": ["A", "B", "A", "B", "C"]})
    assert relaciones_categoria(items, "categoria").loc["A", "B"] == pytest.approx((1 / 4) / ((2 / 4) * (2 / 4)))


def test_meta_de_modularidad_con_datos_reales():
    v = integrar(preparar(cargar_crudos()))["ventas_items"]; v = v[v.pedido_valido]
    w = coocurrencias(v, "producto_id"); g = grafo(w[w >= COOCURRENCIA_MIN])
    assert modularidad(g, comunidades(g)) > META_MODULARIDAD
