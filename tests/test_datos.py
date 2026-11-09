"""Pruebas básicas de integridad de los datos crudos. Ejecutar: pytest -q"""
import pandas as pd
import pytest

from src.config import RAW, TABLAS

CLAVES = {
    "clientes": "cliente_id", "productos": "producto_id", "pedidos": "pedido_id",
    "pagos": "pago_id", "campanias": "campania_id", "logistica": "envio_id",
}


@pytest.mark.parametrize("tabla", TABLAS)
def test_tabla_existe_y_no_vacia(tabla):
    ruta = RAW / f"{tabla}.csv"
    assert ruta.exists(), f"Falta {ruta}"
    assert len(pd.read_csv(ruta, nrows=5)) > 0


@pytest.mark.parametrize("tabla,clave", CLAVES.items())
def test_clave_presente(tabla, clave):
    cols = pd.read_csv(RAW / f"{tabla}.csv", nrows=0).columns
    assert clave in cols


RELACIONES = [
    ("pedidos", "cliente_id", "clientes"), ("pedidos", "campania_id", "campanias"),
    ("detalle_pedido", "pedido_id", "pedidos"), ("detalle_pedido", "producto_id", "productos"),
    ("pagos", "pedido_id", "pedidos"), ("logistica", "pedido_id", "pedidos"),
    ("opiniones", "pedido_id", "pedidos"), ("opiniones", "cliente_id", "clientes"),
    ("atencion", "cliente_id", "clientes"), ("atencion", "pedido_id", "pedidos"),
    ("devoluciones", "pedido_id", "pedidos"), ("devoluciones", "producto_id", "productos"),
    ("marketing", "cliente_id", "clientes"), ("marketing", "campania_id", "campanias"),
    ("navegacion", "cliente_id", "clientes"), ("inventario", "producto_id", "productos"),
]


@pytest.mark.parametrize("hija,columna,padre", RELACIONES)
def test_integridad_referencial(hija, columna, padre):
    claves_hija = pd.read_csv(RAW / f"{hija}.csv", usecols=[columna])[columna].dropna()
    claves_padre = pd.read_csv(RAW / f"{padre}.csv", usecols=[columna])[columna]
    assert claves_hija.isin(claves_padre).all()


def test_inventario_una_fila_por_producto_y_mes():
    inventario = pd.read_csv(RAW / "inventario.csv").drop_duplicates()
    assert not inventario.duplicated(["producto_id", "mes"]).any()
