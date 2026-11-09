"""Pruebas de reglas de asociación. Ejecutar: pytest -q"""
import pandas as pd
import pytest

from src.features.preparacion import cargar_crudos, integrar, preparar
from src.models.asociacion import ALGORITMOS, canastas, eclat, reglas, validar


def _ejemplo() -> pd.DataFrame:
    filas = [{"A": 1, "B": 1, "C": 0}] * 40 + [{"A": 1, "B": 0, "C": 0}] * 10 + [{"A": 0, "B": 0, "C": 1}] * 50
    return pd.DataFrame(filas).astype(bool)


def _firma(fi: pd.DataFrame) -> dict:
    return {i: round(float(s), 8) for i, s in zip(fi.itemsets, fi.support)}


def test_eclat_calcula_soportes_correctos():
    assert _firma(eclat(_ejemplo(), 0.1)) == {frozenset("A"): 0.5, frozenset("B"): 0.4, frozenset("C"): 0.5, frozenset("AB"): 0.4}


def test_los_tres_algoritmos_coinciden():
    firmas = [_firma(alg(_ejemplo(), 0.05)) for alg in ALGORITMOS.values()]
    assert firmas[0] == firmas[1] == firmas[2]


def test_metricas_de_una_regla_conocida():
    r = reglas(_ejemplo(), 0.1)
    fila = r[(r.antecedente == "B") & (r.consecuente == "A")].iloc[0]
    assert fila.soporte == pytest.approx(0.4) and fila.confianza == pytest.approx(1.0) and fila.lift == pytest.approx(2.0)


def test_canastas_excluyen_pedidos_invalidos():
    items = pd.DataFrame({"pedido_id": ["a", "a", "b"], "subcategoria": ["X", "Y", "X"], "pedido_valido": [True, True, False]})
    c = canastas(items)
    assert list(c.index) == ["a"] and c.loc["a"].all()


def test_validar_calcula_sobre_datos_de_prueba():
    r = reglas(_ejemplo(), 0.1); v = validar(r, _ejemplo())
    assert v.lift_prueba.values == pytest.approx(r.lift.values)


def test_datos_reales_tienen_resultados_identicos():
    limpios = preparar(cargar_crudos()); c = canastas(integrar(limpios)["ventas_items"])
    conjuntos = [_firma(alg(c, 0.01)) for alg in ALGORITMOS.values()]
    assert conjuntos[0] == conjuntos[1] == conjuntos[2] and len(conjuntos[0]) > 20
