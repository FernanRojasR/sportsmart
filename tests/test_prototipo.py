"""Pruebas del prototipo Streamlit. Ejecutar: pytest -q"""
from pathlib import Path

import pandas as pd
import pytest
from streamlit.testing.v1 import AppTest

from frontend import datos

PAGINAS = ("Resumen", "Segmentación", "Asociación", "Pronóstico", "Regresión", "Grafos", "Evaluación")


def _reglas():
    return pd.DataFrame({"antecedente": ["A", "A", "B + C", "A"], "consecuente": ["X", "Y", "X", "Z"], "soporte": [.1, .2, .1, .1], "confianza": [.5, .4, .5, .3], "lift": [3.0, 5.0, 4.0, 2.0], "redundante": [False, False, False, True]})


def test_recomendaciones_ordena_y_excluye_redundantes():
    r = datos.recomendaciones(_reglas(), "A")
    assert r.consecuente.tolist() == ["Y", "X"]


def test_recomendaciones_filtra_por_lift():
    assert datos.recomendaciones(_reglas(), "A", 4.0).consecuente.tolist() == ["Y"]


def test_subcategorias_separa_antecedentes_compuestos():
    assert datos.subcategorias_con_reglas(_reglas()) == ["A", "B", "C"]


def test_buscar_cliente_normaliza_el_codigo():
    seg = pd.DataFrame({"cliente_id": ["C00001"], "segmento": ["Alto valor activos"]})
    assert datos.buscar_cliente(seg, " c00001 ").segmento == "Alto valor activos" and datos.buscar_cliente(seg, "C9") is None


def test_real_vs_prediccion_filtra_y_agrega():
    p = pd.DataFrame({"mes": ["m1", "m1", "m1"], "categoria": ["a", "a", "b"], "producto_id": ["p1", "p2", "p3"], "ventas": [1, 2, 4], "prediccion": [2, 2, 5]})
    assert datos.real_vs_prediccion(p, "a").ventas.tolist() == [3] and datos.real_vs_prediccion(p, producto="p3").prediccion.tolist() == [5]


@pytest.mark.parametrize("h", datos.HORIZONTES)
def test_resumen_de_cada_horizonte(h):
    r = datos.resumen_horizonte(datos.leer_json("series"), h)
    assert r["limite_inferior_80"] < r["pronostico"] < r["limite_superior_80"]


@pytest.mark.parametrize("pagina", PAGINAS)
def test_cada_pagina_abre_sin_errores(pagina):
    at = AppTest.from_file(str(Path(__file__).resolve().parents[1] / "frontend" / "app.py"), default_timeout=60).run()
    at.sidebar.radio[0].set_value(pagina).run()
    assert not at.exception, at.exception
