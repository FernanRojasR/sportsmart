"""Pruebas de la construcción de variables. Ejecutar: pytest -q"""
import pandas as pd
import pytest
from pandas.testing import assert_frame_equal

from src.features.preparacion import cargar_crudos, integrar, preparar
from src.features.seleccion import eliminar_colinealidad
from src.features.variables import CORTE_ABANDONO, CORTE_FINAL, FECHAS, NECESARIAS, abc_xyz, agregar_rfm_clv, dataset_abandono, panel_producto_mes, serie_diaria, variables_cliente


@pytest.fixture(scope="module")
def tablas():
    limpios = preparar(cargar_crudos())
    t = {**limpios, **integrar(limpios)}
    t = {n: t[n].copy() for n in NECESARIAS}
    for n, cols in FECHAS.items():
        for c in cols:
            t[n][c] = pd.to_datetime(t[n][c])
    return t


def test_sin_fuga_de_informacion(tablas):
    """Borrar todo lo posterior al corte no debe cambiar ninguna variable."""
    c = CORTE_ABANDONO
    pasado = dict(tablas)
    pasado["pedidos_integrados"] = tablas["pedidos_integrados"].query("fecha_pedido < @c")
    pasado["ventas_items"] = tablas["ventas_items"].query("fecha_pedido < @c")
    pasado["devoluciones"] = tablas["devoluciones"].query("fecha_devolucion < @c")
    pasado["atencion"] = tablas["atencion"].query("fecha < @c")
    pasado["opiniones"] = tablas["opiniones"].query("fecha < @c")
    pasado["navegacion"] = tablas["navegacion"][tablas["navegacion"].mes < c.strftime("%Y-%m")]
    pasado["campanias"] = tablas["campanias"].query("fecha_inicio < @c")
    a = variables_cliente(tablas, c).sort_values("cliente_id").reset_index(drop=True)
    b = variables_cliente(pasado, c).sort_values("cliente_id").reset_index(drop=True)
    assert_frame_equal(a, b)


def test_una_fila_por_cliente(tablas):
    v = variables_cliente(tablas, CORTE_FINAL)
    assert v.cliente_id.is_unique
    assert (v.frecuencia >= 1).all() and (v.recencia >= 0).all()


def test_puntajes_rfm_entre_1_y_5(tablas):
    v = agregar_rfm_clv(variables_cliente(tablas, CORTE_FINAL), 0.46)
    for c in ("r_score", "f_score", "m_score", "l_score"):
        assert v[c].between(1, 5).all()
    assert v.loc[v.recencia.idxmin(), "r_score"] == 5


def test_etiqueta_de_abandono(tablas):
    d = dataset_abandono(tablas)
    ped = tablas["pedidos_integrados"]
    futuros = ped[ped.pedido_valido & (ped.fecha_pedido >= CORTE_ABANDONO)].cliente_id
    assert (d.abandona == (~d.cliente_id.isin(futuros)).astype(int)).all()
    assert (d.recencia <= 180).all()


def test_serie_y_panel_cuadran_con_ventas_validas(tablas):
    ped = tablas["pedidos_integrados"]
    total = ped.loc[ped.pedido_valido, "monto_total"].sum()
    assert serie_diaria(tablas).ventas.sum() == pytest.approx(total, abs=0.05)
    assert panel_producto_mes(tablas).ventas.sum() == pytest.approx(total, abs=0.5)


def test_panel_rezagos_solo_miran_al_pasado(tablas):
    p = panel_producto_mes(tablas)
    assert len(p) == 321 * 45
    prod = p[p.producto_id == p.producto_id.iloc[0]].sort_values("mes")
    assert prod.ventas_lag1.iloc[1:].tolist() == prod.ventas.iloc[:-1].tolist()


def test_abc_xyz_clasifica_todo_el_catalogo(tablas):
    r = abc_xyz(tablas)
    assert len(r) == 321 and set(r.abc) <= {"A", "B", "C"} and set(r.xyz) <= {"X", "Y", "Z"}


def test_eliminar_colinealidad_retira_la_menos_asociada():
    x = pd.DataFrame({"a": range(50), "b": [i * 2 for i in range(50)], "c": [i % 7 for i in range(50)]})
    y = pd.Series([i % 7 for i in range(50)])
    conservadas, detalle = eliminar_colinealidad(x, y)
    assert len(detalle) == 1 and "c" in conservadas and len(conservadas) == 2
