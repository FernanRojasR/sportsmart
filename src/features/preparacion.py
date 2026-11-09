"""Limpieza e integración de los datos crudos de SportSmart Perú.

Aplica los tratamientos de docs/02_datos/informe_calidad.md en el orden allí definido,
sin modificar data/raw. Escribe las tablas limpias y las vistas integradas en data/processed
y el resultado de los controles en reports/preparacion.json.

Uso:  python -m src.features.preparacion
"""
import json

import numpy as np
import pandas as pd

from src.config import PROCESSED, RAW, REPORTS, TABLAS

DEPARTAMENTOS = {"Lima", "Arequipa", "La Libertad", "Piura", "Lambayeque", "Cusco", "Junín", "Ica", "Áncash", "Callao", "Puno", "Loreto"}
VARIANTES_DEPARTAMENTO = {"Junin": "Junín", "Ancash": "Áncash", "Cuzco": "Cusco"}
EDAD_MIN, EDAD_MAX = 16, 90
CANTIDAD_MAX = 10              # el catálogo vende entre 1 y 3 unidades; más de 10 es anómalo
DIAS_ENTREGA_MAX = 40
RECIBIDAS_ATIPICAS = 5000
FECHA_FUTURA = pd.Timestamp("2026-10-12")  # posterior a cualquier dato real del periodo
FIN_PERIODO = pd.Timestamp("2026-10-01")   # exclusivo: el periodo cierra el 2026-09-30
TOLERANCIA_SOLES = 0.05

# Problemas que se conservan a propósito tras la limpieza
SE_CONSERVA = {"Q18": "Sin texto: se excluye solo de NLP y se mantiene la puntuación"}


def cargar_crudos() -> dict[str, pd.DataFrame]:
    return {t: pd.read_csv(RAW / f"{t}.csv") for t in TABLAS}


def _balance_inventario(iv: pd.DataFrame) -> pd.Series:
    return iv.stock_inicial + iv.unidades_recibidas + iv.reposicion_urgente - iv.unidades_vendidas + iv.unidades_reingresadas


def controles(t: dict[str, pd.DataFrame]) -> dict[str, int]:
    """Cuenta cada problema Q01-Q23 del informe de calidad. Se aplica igual antes y después."""
    c, pr, p, d, pg, lg, o, a, iv = (t[k] for k in ("clientes", "productos", "pedidos", "detalle_pedido", "pagos", "logistica", "opiniones", "atencion", "inventario"))
    fechas = pd.to_datetime(p.fecha_pedido)
    pago = pg.merge(p[["pedido_id", "monto_total"]], on="pedido_id")
    return {
        "Q01": int((fechas > FECHA_FUTURA).sum()),
        "Q02": int((~c.departamento.isin(DEPARTAMENTOS)).sum()),
        "Q03": int((c.genero.notna() & ~c.genero.isin(["M", "F", "No declarado"])).sum()),
        "Q04": int(c.duplicated().sum()),
        "Q05": int(d.duplicated().sum()),
        "Q06": int(p.monto_total.isna().sum()),
        "Q07": int((d.cantidad <= 0).sum()),
        "Q08": int((d.cantidad > CANTIDAD_MAX).sum()),
        "Q09": int(((pago.importe - pago.monto_total).abs() > TOLERANCIA_SOLES).sum()),
        "Q10": int(c.edad.isna().sum()),
        "Q11": int(((c.edad < EDAD_MIN) | (c.edad > EDAD_MAX)).sum()),
        "Q12": int((lg.dias_entrega > DIAS_ENTREGA_MAX).sum()),
        "Q13": int((o.puntuacion.notna() & ~o.puntuacion.between(1, 5)).sum()),
        "Q14": int((iv.unidades_recibidas.isna() | (iv.unidades_recibidas >= RECIBIDAS_ATIPICAS)).sum()),
        "Q15": int((iv.stock_final.isna() | (iv.stock_final < 0)).sum()),
        "Q16": int(iv.duplicated().sum()),
        "Q17": int(pr.precio_lista.isna().sum()),
        "Q18": int(o.comentario.fillna("").str.strip().eq("").sum()),
        "Q19": int((c.genero.isna()).sum()),
        "Q20": int(pg.metodo.isna().sum()),
        "Q21": int((lg.distancia_km < 0).sum()),
        "Q22": int((a.horas_resolucion < 0).sum()),
        "Q23": int(pr.marca.isna().sum()),
    }


def preparar(crudos: dict[str, pd.DataFrame]) -> dict[str, pd.DataFrame]:
    """Devuelve copias limpias de las 13 tablas."""
    t = {k: v.copy() for k, v in crudos.items()}
    c, pr, p, d, pg, lg, o, a, iv = (t[k] for k in ("clientes", "productos", "pedidos", "detalle_pedido", "pagos", "logistica", "opiniones", "atencion", "inventario"))

    # Paso 1. Duplicados (Q04, Q05, Q16): primero, para no sumar importes repetidos
    c = c.drop_duplicates("cliente_id").reset_index(drop=True)
    d = d.drop_duplicates().reset_index(drop=True)
    iv = iv.drop_duplicates().sort_values(["producto_id", "mes"]).reset_index(drop=True)

    # Paso 2. Cantidades (Q07, Q08), montos (Q06) e importes de pago (Q09)
    anomala = (d.cantidad <= 0) | (d.cantidad > CANTIDAD_MAX)
    d["cantidad_corregida"] = anomala
    d.loc[anomala, "cantidad"] = (d.importe[anomala] / (d.precio_unitario[anomala] * (1 - d.descuento[anomala]))).round()
    d["cantidad"] = d.cantidad.astype(int)
    suma_detalle = d.groupby("pedido_id").importe.sum().round(2)
    p["monto_reconstruido"] = p.monto_total.isna()
    p["monto_total"] = p.monto_total.fillna(p.pedido_id.map(suma_detalle))
    monto = pg.pedido_id.map(p.set_index("pedido_id").monto_total)
    pg["importe_ajustado"] = (pg.importe - monto).abs() > TOLERANCIA_SOLES
    pg.loc[pg.importe_ajustado, "importe"] = monto[pg.importe_ajustado]

    # Paso 3. Fechas futuras (Q01): el envío se registra el día siguiente al pedido
    p["fecha_pedido"] = pd.to_datetime(p.fecha_pedido)
    futura = p.fecha_pedido > FECHA_FUTURA
    p["fecha_reconstruida"] = futura
    envio = pd.to_datetime(p.pedido_id.map(lg.set_index("pedido_id").fecha_envio))
    p.loc[futura, "fecha_pedido"] = envio[futura] - pd.Timedelta(days=1)
    p["con_campania"] = p.campania_id.notna()
    p["pedido_valido"] = (p.estado != "Cancelado") & (p.fecha_pedido < FIN_PERIODO)

    # Paso 4. Categorías (Q02, Q03, Q19, Q20, Q23)
    c["departamento"] = c.departamento.str.strip().str.title().replace(VARIANTES_DEPARTAMENTO)
    c["genero"] = c.genero.str.strip().str.upper().str[0].fillna("No declarado")
    pg["metodo"] = pg.metodo.fillna("No registrado")
    pr["marca"] = pr.marca.fillna("Sin marca")

    # Paso 5. Valores inválidos (Q11-Q13, Q21, Q22) y reconstrucciones (Q14, Q15, Q17)
    c.loc[~c.edad.between(EDAD_MIN, EDAD_MAX), "edad"] = np.nan
    extremo = lg.dias_entrega > DIAS_ENTREGA_MAX
    lg["dias_entrega_imputado"] = extremo
    lg.loc[extremo, "dias_entrega"] = np.nan
    o.loc[~o.puntuacion.between(1, 5), "puntuacion"] = np.nan
    o["comentario"] = o.comentario.where(o.comentario.fillna("").str.strip() != "")
    o["tiene_comentario"] = o.comentario.notna()
    lg["distancia_km"] = lg.distancia_km.abs()
    a["horas_resolucion"] = a.horas_resolucion.abs()
    pr["precio_lista"] = pr.precio_lista.fillna(pr.producto_id.map(d.groupby("producto_id").precio_unitario.first()))

    nulo_o_atipico = iv.unidades_recibidas.isna() | (iv.unidades_recibidas >= RECIBIDAS_ATIPICAS)
    negativo = iv.stock_final < 0
    recibidas = iv.stock_final - iv.stock_inicial - iv.reposicion_urgente + iv.unidades_vendidas - iv.unidades_reingresadas
    final = _balance_inventario(iv)
    iv["registro_reconstruido"] = (nulo_o_atipico & ~negativo & (recibidas >= 0)) | (negativo & ~nulo_o_atipico & (final >= 0))
    iv.loc[nulo_o_atipico, "unidades_recibidas"] = recibidas.where(~negativo & (recibidas >= 0))[nulo_o_atipico]
    iv.loc[negativo, "stock_final"] = final.where(~nulo_o_atipico & (final >= 0))[negativo]

    # Paso 6. Imputaciones (Q10, Q12). Los modelos deben rehacerlas solo con datos de entrenamiento,
    # usando estas banderas para restituir los faltantes.
    c["edad_faltante"] = c.edad.isna()
    c["edad"] = c.edad.fillna(c.edad.median())
    zona = lg.pedido_id.map(p.set_index("pedido_id").cliente_id).map(c.set_index("cliente_id").departamento).isin(["Lima", "Callao"])
    lg.loc[extremo, "dias_entrega"] = lg.dias_entrega.fillna(lg.groupby(zona).dias_entrega.transform("median"))[extremo]

    t.update(clientes=c, productos=pr, pedidos=p, detalle_pedido=d, pagos=pg, logistica=lg, opiniones=o, atencion=a, inventario=iv)
    return t


def integrar(t: dict[str, pd.DataFrame]) -> dict[str, pd.DataFrame]:
    """Vistas integradas para modelar: una fila por ítem vendido y una por pedido."""
    clientes = t["clientes"][["cliente_id", "edad", "edad_faltante", "genero", "departamento", "fecha_registro", "canal_adquisicion", "deporte_preferido"]]
    productos = t["productos"].drop(columns="nombre")
    pedidos = t["pedidos"]
    items = (t["detalle_pedido"]
             .merge(pedidos[["pedido_id", "cliente_id", "fecha_pedido", "campania_id", "estado", "pedido_valido"]], on="pedido_id", how="left", validate="m:1")
             .merge(productos, on="producto_id", how="left", validate="m:1")
             .merge(clientes, on="cliente_id", how="left", validate="m:1"))
    pago = t["pagos"][["pedido_id", "metodo", "cuotas", "estado_pago", "importe_ajustado"]]
    envio = t["logistica"][["pedido_id", "operador", "distancia_km", "costo_envio", "dias_entrega", "dias_prometidos", "entrega_a_tiempo", "dias_entrega_imputado"]]
    ped = (pedidos.merge(clientes, on="cliente_id", how="left", validate="m:1")
           .merge(pago, on="pedido_id", how="left", validate="1:1")
           .merge(envio, on="pedido_id", how="left", validate="1:1"))
    return {"ventas_items": items, "pedidos_integrados": ped}


def coherencia(t: dict[str, pd.DataFrame]) -> dict[str, int]:
    """Controles entre tablas sobre los datos limpios; todos deben dar 0."""
    p, d, iv = t["pedidos"], t["detalle_pedido"], t["inventario"]
    suma = d.groupby("pedido_id").importe.sum()
    calculado = d.cantidad * d.precio_unitario * (1 - d.descuento)
    fecha = p.set_index("pedido_id").fecha_pedido
    envio = t["logistica"]; opi = t["opiniones"]
    ventas = d.merge(p.loc[p.estado != "Cancelado", ["pedido_id", "fecha_pedido"]], on="pedido_id")
    unidades = ventas.groupby(["producto_id", ventas.fecha_pedido.dt.strftime("%Y-%m").rename("mes")]).cantidad.sum()
    inventario = iv.set_index(["producto_id", "mes"]).unidades_vendidas
    balance = _balance_inventario(iv).dropna(); balance = balance[iv.stock_final[balance.index].notna()]
    return {
        "monto_distinto_a_detalle": int(((p.set_index("pedido_id").monto_total - suma).abs() > TOLERANCIA_SOLES).sum()),
        "importe_distinto_a_cantidad_por_precio": int(((calculado - d.importe).abs() > TOLERANCIA_SOLES).sum()),
        "envio_antes_de_pedido": int((pd.to_datetime(envio.fecha_envio) < envio.pedido_id.map(fecha).dt.normalize()).sum()),
        "opinion_antes_de_pedido": int((pd.to_datetime(opi.fecha) < opi.pedido_id.map(fecha).dt.normalize()).sum()),
        "unidades_inventario_distintas_a_ventas": int((inventario.sub(unidades, fill_value=0) != 0).sum()),
        "balance_inventario_no_cuadra": int((balance != iv.stock_final[balance.index]).sum()),
        "pedidos_fuera_de_periodo_validos": int((p.pedido_valido & (p.fecha_pedido >= FIN_PERIODO)).sum()),
    }


def resumen(crudos: dict[str, pd.DataFrame], limpios: dict[str, pd.DataFrame]) -> dict:
    antes, despues = controles(crudos), controles(limpios)
    p0, p1 = crudos["pedidos"], limpios["pedidos"]
    v0 = p0[(pd.to_datetime(p0.fecha_pedido) < FIN_PERIODO) & (p0.estado != "Cancelado") & p0.monto_total.notna()]
    v1 = p1[p1.pedido_valido]
    return {
        "controles": {q: {"antes": antes[q], "despues": despues[q], **({"nota": SE_CONSERVA[q]} if q in SE_CONSERVA else {})} for q in antes},
        "incidencias_antes": sum(antes.values()),
        "incidencias_despues": sum(despues.values()),
        "coherencia": coherencia(limpios),
        "filas": {k: {"antes": len(crudos[k]), "despues": len(limpios[k])} for k in crudos},
        "ventas_validas": {"pedidos_antes": len(v0), "pedidos_despues": len(v1), "soles_antes": round(float(v0.monto_total.sum()), 2), "soles_despues": round(float(v1.monto_total.sum()), 2),
                           "diferencia_soles": round(float(v1.monto_total.sum() - v0.monto_total.sum()), 2)},
    }


def main() -> dict:
    crudos = cargar_crudos()
    limpios = preparar(crudos)
    vistas = integrar(limpios)
    PROCESSED.mkdir(parents=True, exist_ok=True)
    for nombre, df in {**limpios, **vistas}.items():
        df.to_csv(PROCESSED / f"{nombre}.csv", index=False)
    res = resumen(crudos, limpios)
    res["vistas_integradas"] = {k: {"filas": len(v), "columnas": v.shape[1]} for k, v in vistas.items()}
    REPORTS.mkdir(parents=True, exist_ok=True)
    (REPORTS / "preparacion.json").write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"Incidencias: {res['incidencias_antes']} -> {res['incidencias_despues']}. Tablas en data/processed")
    return res


if __name__ == "__main__":
    main()
