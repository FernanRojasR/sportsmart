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


def test_integridad_pedidos_clientes():
    pedidos = pd.read_csv(RAW / "pedidos.csv", usecols=["cliente_id"])
    clientes = pd.read_csv(RAW / "clientes.csv", usecols=["cliente_id"])
    huerfanos = ~pedidos.cliente_id.isin(clientes.cliente_id)
    assert huerfanos.mean() < 0.01
