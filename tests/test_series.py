"""Pruebas de series temporales. Ejecutar: pytest -q"""
import numpy as np
import pandas as pd
import pytest

from src.models.series import MODELOS, _semanal, calendario, metricas, pronosticar


def _serie(dias: int = 500) -> pd.Series:
    idx = pd.date_range("2024-01-01", periods=dias, freq="D")
    return pd.Series(1000 + 200 * (idx.day_of_week >= 5) + np.arange(dias) * 0.5, idx, dtype=float)


def test_metricas_de_pronostico_perfecto():
    y = _serie(70)
    m = metricas(y, y.values)
    assert m["mape_diario"] == 0 and m["mape_semanal"] == 0 and m["r2_diario"] == 1


def test_mape_diario_conocido():
    y = pd.Series([100.0, 200.0], pd.date_range("2024-01-01", periods=2, freq="D"))
    assert metricas(y, np.array([110.0, 180.0]))["mape_diario"] == pytest.approx(10.0)


def test_semanal_excluye_semanas_incompletas():
    idx = pd.date_range("2024-01-03", periods=20, freq="D")  # empieza miércoles
    s = _semanal(idx, np.ones(20))
    assert (s == 7).all() and len(s) == 2


def test_calendario_marca_quincenas_y_campanias():
    idx = pd.date_range("2024-01-14", periods=3, freq="D")
    x = calendario(idx, pd.Series([0.0, 0.2, 0.0], idx))
    assert x.quincena.tolist() == [0, 1, 1] and x.descuento_campania.tolist() == [0.0, 0.2, 0.0]


def test_referencia_usa_el_mismo_dia_de_hace_52_semanas():
    y = _serie(400); fut = pd.date_range(y.index[-1] + pd.Timedelta(days=1), periods=7, freq="D")
    ex_fut = calendario(fut, pd.Series(0.0, fut))
    f = pronosticar(MODELOS[0], y, calendario(y.index, pd.Series(0.0, y.index)), ex_fut, {})
    assert f.tolist() == y.reindex(fut - pd.Timedelta(days=364)).tolist()


@pytest.mark.parametrize("modelo", ["SARIMA", "SARIMAX", "Prophet"])
def test_modelos_devuelven_un_valor_por_dia(modelo):
    y = _serie(); fut = pd.date_range(y.index[-1] + pd.Timedelta(days=1), periods=14, freq="D")
    f = pronosticar(modelo, y, calendario(y.index, pd.Series(0.0, y.index)), calendario(fut, pd.Series(0.0, fut)), {"SARIMA": (1, 0, 1), "SARIMAX": (1, 0, 1)})
    assert len(f) == 14 and np.isfinite(f).all() and (f > 0).all()
