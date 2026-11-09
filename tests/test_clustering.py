"""Pruebas de la segmentación. Ejecutar: pytest -q"""
import numpy as np
import pandas as pd
import pytest

from src.features.preparacion import cargar_crudos, integrar, preparar
from src.features.variables import CORTE_FINAL, FECHAS, NECESARIAS, agregar_rfm_clv, variables_cliente
from src.models.clustering import K_ELEGIDO, META_SILUETA, RFM, _kmeans, _nombrar, _silueta, matriz


@pytest.fixture(scope="module")
def clientes():
    limpios = preparar(cargar_crudos()); t = {**limpios, **integrar(limpios)}
    t = {n: t[n].copy() for n in NECESARIAS}
    for n, cols in FECHAS.items():
        for c in cols:
            t[n][c] = pd.to_datetime(t[n][c])
    return agregar_rfm_clv(variables_cliente(t, CORTE_FINAL), 0.46)


def test_matriz_estandarizada():
    df = pd.DataFrame({"a": [1, 10, 100, 1000], "b": [0, 5, 2, 9]})
    x = matriz(df, ["a", "b"])
    assert np.allclose(x.mean(axis=0), 0) and np.allclose(x.std(axis=0), 1)


def test_nombres_dependen_del_comportamiento_y_no_del_orden():
    perfil = pd.DataFrame({"recencia": [600, 20, 580], "monetario": [300, 2200, 2100]}, index=[0, 1, 2])
    assert _nombrar(perfil) == {1: "Alto valor activos", 2: "Valiosos inactivos", 0: "Ocasionales inactivos"}


def test_meta_de_silhouette_con_tres_segmentos(clientes):
    x = matriz(clientes, RFM)
    assert _silueta(x, _kmeans(K_ELEGIDO).fit_predict(x)) > META_SILUETA


def test_segmentacion_reproducible(clientes):
    x = matriz(clientes, RFM)
    assert (_kmeans(K_ELEGIDO).fit_predict(x) == _kmeans(K_ELEGIDO).fit_predict(x)).all()
