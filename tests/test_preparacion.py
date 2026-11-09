"""Comprueba que la preparación resuelve los problemas del informe de calidad. Ejecutar: pytest -q"""
import pandas as pd
import pytest

from src.features.preparacion import cargar_crudos, coherencia, controles, integrar, preparar

CONSERVADOS = {"Q18"}             # comentarios vacíos: se conservan a propósito
RESIDUALES = {"Q14": 1, "Q15": 1}  # el informe anticipa un caso no recuperable en cada uno


@pytest.fixture(scope="module")
def crudos():
    return cargar_crudos()


@pytest.fixture(scope="module")
def limpios(crudos):
    return preparar(crudos)


def test_controles_crudos_coinciden_con_el_informe(crudos):
    esperado = {"Q01": 25, "Q02": 752, "Q03": 580, "Q04": 45, "Q05": 120, "Q06": 60, "Q07": 20, "Q08": 20, "Q09": 80, "Q10": 901, "Q11": 14, "Q12": 20,
                "Q13": 15, "Q14": 49, "Q15": 20, "Q16": 30, "Q17": 5, "Q18": 1145, "Q19": 452, "Q20": 634, "Q21": 30, "Q22": 12, "Q23": 3}
    obtenido = controles(crudos)
    for clave, valor in esperado.items():
        if clave in ("Q14", "Q15"):
            continue  # el informe los mide tras quitar duplicados
        assert obtenido[clave] == valor, clave


def test_problemas_resueltos(limpios):
    despues = controles(limpios)
    for clave, valor in despues.items():
        if clave not in CONSERVADOS:
            assert valor == RESIDUALES.get(clave, 0), clave


def test_comentarios_vacios_se_conservan(limpios):
    assert controles(limpios)["Q18"] == 1145


@pytest.mark.parametrize("control", ["monto_distinto_a_detalle", "importe_distinto_a_cantidad_por_precio", "envio_antes_de_pedido", "opinion_antes_de_pedido",
                                     "unidades_inventario_distintas_a_ventas", "balance_inventario_no_cuadra", "pedidos_fuera_de_periodo_validos"])
def test_coherencia_entre_tablas(limpios, control):
    assert coherencia(limpios)[control] == 0


def test_no_se_pierden_entidades(crudos, limpios):
    assert limpios["clientes"].cliente_id.nunique() == crudos["clientes"].cliente_id.nunique()
    assert len(limpios["pedidos"]) == len(crudos["pedidos"])
    assert not limpios["clientes"].cliente_id.duplicated().any()


def test_los_crudos_no_se_modifican(crudos):
    assert crudos["pedidos"].monto_total.isna().sum() == 60
    assert "edad_faltante" not in crudos["clientes"].columns


def test_vistas_integradas_conservan_el_grano(limpios):
    vistas = integrar(limpios)
    assert len(vistas["ventas_items"]) == len(limpios["detalle_pedido"])
    assert len(vistas["pedidos_integrados"]) == len(limpios["pedidos"])
    assert vistas["ventas_items"].categoria.notna().all()


def test_ventas_recuperadas_coinciden_con_el_informe(crudos, limpios):
    p0, p1 = crudos["pedidos"], limpios["pedidos"]
    antes = p0[(pd.to_datetime(p0.fecha_pedido) < "2026-10-01") & (p0.estado != "Cancelado") & p0.monto_total.notna()].monto_total.sum()
    assert p1[p1.pedido_valido].monto_total.sum() - antes == pytest.approx(19885.95, abs=0.05)
