"""Pruebas de regresión. Ejecutar: pytest -q"""
import numpy as np
import pandas as pd
import pytest
from sklearn.linear_model import Ridge
from sklearn.metrics import r2_score
from sklearn.pipeline import Pipeline

from src.features.preparacion import cargar_crudos, integrar, preparar
from src.features.variables import FECHAS, NECESARIAS, panel_producto_mes
from src.models.regresion import CATEGORICAS, INICIO_ENTRENAMIENTO, INICIO_PRUEBA, META_R2, NUMERICAS, VARIABLES, metricas, pliegues_temporales, preparador


def test_metricas_conocidas():
    m = metricas([100, 200], [110, 190])
    assert m["mae"] == 10 and m["rmse"] == 10 and m["wape_pct"] == pytest.approx(6.7)


def test_pliegues_validan_siempre_con_meses_posteriores():
    meses = pd.Series([f"2025-{m:02d}" for m in range(1, 13) for _ in range(3)])
    pliegues = pliegues_temporales(meses)
    assert len(pliegues) == 3
    for tr, va in pliegues:
        assert meses.iloc[tr].max() < meses.iloc[va].min()


def test_variables_explicativas_no_incluyen_el_objetivo():
    assert "ventas" not in VARIABLES and "unidades" not in VARIABLES


def test_preparador_imputa_y_codifica():
    x = pd.DataFrame({"a": [1.0, np.nan, 3.0], "c": ["x", "y", "x"]})
    salida = preparador(["a"], ["c"]).fit_transform(x)
    assert salida.shape == (3, 3) and not np.isnan(salida).any()


def test_meta_de_r2_con_datos_reales():
    limpios = preparar(cargar_crudos()); t = {**limpios, **integrar(limpios)}
    t = {n: t[n].copy() for n in NECESARIAS}
    for n, cols in FECHAS.items():
        for c in cols:
            t[n][c] = pd.to_datetime(t[n][c])
    p = panel_producto_mes(t); d = p[p.mes >= INICIO_ENTRENAMIENTO]; tr, te = d[d.mes < INICIO_PRUEBA], d[d.mes >= INICIO_PRUEBA]
    m = Pipeline([("pre", preparador(NUMERICAS, CATEGORICAS)), ("m", Ridge(alpha=1))]).fit(tr[VARIABLES], tr.ventas)
    assert r2_score(te.ventas, m.predict(te[VARIABLES])) > META_R2
