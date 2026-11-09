"""Construcción de variables a partir de data/processed.

Las variables por cliente se calculan con una fecha de corte y usan solo hechos anteriores a ella,
para evitar fuga de información. Uso:  python -m src.features.variables
"""
import numpy as np
import pandas as pd

from src.config import PROCESSED

CORTE_FINAL = pd.Timestamp("2026-10-01")     # exclusivo: el periodo cierra el 2026-09-30
DIAS_ABANDONO = 180                          # sustentado en el EDA: 97,6 % de las recompras ocurre en 180 días o menos
CORTE_ABANDONO = CORTE_FINAL - pd.Timedelta(days=DIAS_ABANDONO)
TASA_DESCUENTO_CLV = 0.10                    # supuesto del equipo
INICIO, FIN = pd.Timestamp("2023-01-01"), pd.Timestamp("2026-09-30")
FECHAS = {"clientes": ["fecha_registro"], "ventas_items": ["fecha_pedido"], "pedidos_integrados": ["fecha_pedido"], "devoluciones": ["fecha_devolucion"],
          "atencion": ["fecha"], "opiniones": ["fecha"], "campanias": ["fecha_inicio", "fecha_fin"]}
NECESARIAS = ["clientes", "productos", "ventas_items", "pedidos_integrados", "devoluciones", "atencion", "opiniones", "marketing", "campanias", "navegacion", "inventario"]


def cargar_procesados() -> dict[str, pd.DataFrame]:
    return {n: pd.read_csv(PROCESSED / f"{n}.csv", parse_dates=FECHAS.get(n, [])) for n in NECESARIAS}


def _quintil(s: pd.Series, invertir: bool = False) -> pd.Series:
    """Puntaje de 1 a 5; rank(first) reparte los empates para formar grupos del mismo tamaño."""
    q = pd.qcut(s.rank(method="first"), 5, labels=False) + 1
    return (6 - q if invertir else q).astype(int)


def variables_cliente(t: dict[str, pd.DataFrame], corte: pd.Timestamp) -> pd.DataFrame:
    """Una fila por cliente con al menos una compra válida antes de `corte` (exclusivo)."""
    ped = t["pedidos_integrados"]; ped = ped[ped.pedido_valido & (ped.fecha_pedido < corte)]
    ite = t["ventas_items"]; ite = ite[ite.pedido_valido & (ite.fecha_pedido < corte)].copy()
    referencia = corte - pd.Timedelta(days=1)
    g = ped.groupby("cliente_id")
    v = g.agg(frecuencia=("pedido_id", "size"), monetario=("monto_total", "sum"), ticket_medio=("monto_total", "mean"), ticket_max=("monto_total", "max"),
              primera=("fecha_pedido", "min"), ultima=("fecha_pedido", "max"), pct_con_campania=("con_campania", "mean"), dias_entrega_medio=("dias_entrega", "mean"))
    v["recencia"] = (referencia - v.ultima).dt.days.clip(lower=0)
    v["longitud"] = (v.ultima - v.primera).dt.days
    v["compra_unica"] = (v.frecuencia == 1).astype(int)
    v["intervalo_medio"] = (v.longitud / (v.frecuencia - 1)).where(v.frecuencia > 1, 0.0)
    for dias in (180, 365):
        rec = ped[ped.fecha_pedido >= corte - pd.Timedelta(days=dias)].groupby("cliente_id")
        v[f"frecuencia_{dias}d"] = rec.size().reindex(v.index).fillna(0)
        v[f"monetario_{dias}d"] = rec.monto_total.sum().reindex(v.index).fillna(0)
    v["pct_retraso"] = ped.assign(r=ped.entrega_a_tiempo.astype(str).eq("False")).groupby("cliente_id").r.mean().reindex(v.index)
    # Productos y margen
    ite["margen"] = ite.importe - ite.costo * ite.cantidad
    gi = ite.groupby("cliente_id")
    v["items"] = gi.size(); v["n_categorias"] = gi.categoria.nunique(); v["n_subcategorias"] = gi.subcategoria.nunique()
    v["descuento_medio"] = gi.descuento.mean(); v["margen_total"] = gi.margen.sum()
    # Postventa
    dv = t["devoluciones"]; dv = dv[dv.fecha_devolucion < corte].merge(t["pedidos_integrados"][["pedido_id", "cliente_id"]], on="pedido_id")
    v["devoluciones"] = dv.groupby("cliente_id").size().reindex(v.index).fillna(0)
    v["tasa_devolucion"] = v.devoluciones / v["items"]
    at = t["atencion"]; at = at[at.fecha < corte].groupby("cliente_id")
    v["tickets"] = at.size().reindex(v.index).fillna(0)
    v["reclamos"] = t["atencion"].query("fecha < @corte and tipo == 'Reclamo'").groupby("cliente_id").size().reindex(v.index).fillna(0)
    op = t["opiniones"]; op = op[op.fecha < corte]
    v["puntuacion_media"] = op.groupby("cliente_id").puntuacion.mean().reindex(v.index)
    v["tiene_opinion"] = v.puntuacion_media.notna().astype(int)
    # Marketing y navegación: solo lo ocurrido antes del corte
    vistas = t["campanias"].loc[t["campanias"].fecha_inicio < corte, "campania_id"]
    mk = t["marketing"]; mk = mk[mk.campania_id.isin(vistas)].groupby("cliente_id")
    v["campanias_recibidas"] = mk.size().reindex(v.index).fillna(0)
    v["tasa_apertura"] = mk.abrio.mean().reindex(v.index).fillna(0); v["tasa_clic"] = mk.hizo_clic.mean().reindex(v.index).fillna(0)
    nv = t["navegacion"]; nv = nv[(nv.mes < corte.strftime("%Y-%m"))].groupby("cliente_id")[["sesiones", "paginas_vistas", "minutos_totales", "carritos_abandonados"]].sum()
    v = v.join(nv)
    v["tiene_navegacion"] = v.sesiones.notna().astype(int)
    v[["sesiones", "paginas_vistas", "minutos_totales", "carritos_abandonados"]] = v[["sesiones", "paginas_vistas", "minutos_totales", "carritos_abandonados"]].fillna(0)
    # Perfil
    c = t["clientes"].set_index("cliente_id")
    v = v.join(c[["edad", "edad_faltante", "genero", "departamento", "canal_adquisicion", "deporte_preferido", "fecha_registro"]])
    v["antiguedad"] = (referencia - v.fecha_registro).dt.days.clip(lower=0)
    v["zona"] = np.where(v.departamento.isin(["Lima", "Callao"]), "Lima/Callao", "Provincias")
    return v.drop(columns=["primera", "ultima", "fecha_registro"]).reset_index()


def retencion_anual(t: dict[str, pd.DataFrame], corte: pd.Timestamp) -> float:
    ped = t["pedidos_integrados"]; ped = ped[ped.pedido_valido]
    a, b = corte - pd.DateOffset(years=2), corte - pd.DateOffset(years=1)
    previos = ped.loc[(ped.fecha_pedido >= a) & (ped.fecha_pedido < b), "cliente_id"].drop_duplicates()
    return float(previos.isin(ped.loc[(ped.fecha_pedido >= b) & (ped.fecha_pedido < corte), "cliente_id"]).mean())


def agregar_rfm_clv(v: pd.DataFrame, retencion: float) -> pd.DataFrame:
    """Puntajes RFM y LRFM de 1 a 5 y CLV = margen anual × r ÷ (1 + d − r)."""
    v = v.copy()
    v["r_score"] = _quintil(v.recencia, invertir=True); v["f_score"] = _quintil(v.frecuencia); v["m_score"] = _quintil(v.monetario); v["l_score"] = _quintil(v.longitud)
    v["rfm_total"] = v.r_score + v.f_score + v.m_score
    v["lrfm_total"] = v.rfm_total + v.l_score
    anios = (v.antiguedad / 365.25).clip(lower=1)  # al menos un año, para no anualizar en exceso a clientes nuevos
    v["margen_anual"] = v.margen_total / anios
    v["clv"] = v.margen_anual * retencion / (1 + TASA_DESCUENTO_CLV - retencion)
    return v


def dataset_abandono(t: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Compradores activos al corte. abandona = 1 si no compra en los 180 días siguientes."""
    x = variables_cliente(t, CORTE_ABANDONO)
    x = x[x.recencia <= DIAS_ABANDONO].copy()
    ped = t["pedidos_integrados"]; ped = ped[ped.pedido_valido & (ped.fecha_pedido >= CORTE_ABANDONO) & (ped.fecha_pedido < CORTE_FINAL)]
    x["abandona"] = (~x.cliente_id.isin(ped.cliente_id)).astype(int)
    return x


def abc_xyz(t: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """ABC por ingresos acumulados (80 % y 95 %) y XYZ por variabilidad de las unidades mensuales."""
    ite = t["ventas_items"]; ite = ite[ite.pedido_valido].copy()
    meses = pd.period_range(INICIO, FIN, freq="M")
    ite["periodo"] = ite.fecha_pedido.dt.to_period("M")
    u = ite.groupby(["producto_id", "periodo"]).cantidad.sum().unstack(fill_value=0).reindex(columns=meses, fill_value=0)
    pr = t["productos"].set_index("producto_id")[["categoria", "subcategoria", "marca", "precio_lista", "costo"]]
    r = pr.join(ite.groupby("producto_id").agg(ingresos=("importe", "sum"), unidades=("cantidad", "sum"))).fillna({"ingresos": 0, "unidades": 0}).sort_values("ingresos", ascending=False)
    cum = r.ingresos.cumsum() / r.ingresos.sum()
    r["abc"] = np.select([cum <= .80, cum <= .95], ["A", "B"], "C")
    u = u.reindex(r.index).fillna(0)
    r["cv_unidades"] = (u.std(axis=1) / u.mean(axis=1)).replace([np.inf], np.nan).fillna(99)
    r["xyz"] = np.select([r.cv_unidades <= .5, r.cv_unidades <= 1], ["X", "Y"], "Z")
    r["abc_xyz"] = r.abc + r.xyz
    return r.reset_index()


def _descuento_activo(campanias: pd.DataFrame, dias: pd.DatetimeIndex) -> pd.Series:
    d = pd.Series(0.0, index=dias)
    for c in campanias.itertuples():
        m = (dias >= c.fecha_inicio) & (dias <= c.fecha_fin)
        d[m] = np.maximum(d[m].values, c.descuento)
    return d


def serie_diaria(t: dict[str, pd.DataFrame]) -> pd.DataFrame:
    ped = t["pedidos_integrados"]; ped = ped[ped.pedido_valido]
    dias = pd.date_range(INICIO, FIN, freq="D")
    g = ped.set_index("fecha_pedido").resample("D")
    s = pd.DataFrame({"ventas": g.monto_total.sum(), "pedidos": g.pedido_id.count()}).reindex(dias, fill_value=0)
    s["descuento_campania"] = _descuento_activo(t["campanias"], dias)
    s["quincena"] = dias.day.isin([1, 15, 16, 30, 31]).astype(int)
    s["fin_de_semana"] = (dias.day_of_week >= 5).astype(int)
    return s.rename_axis("fecha").reset_index()


def panel_producto_mes(t: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Una fila por producto y mes. Toda variable explicativa se conoce antes de empezar el mes."""
    ite = t["ventas_items"]; ite = ite[ite.pedido_valido].copy(); ite["mes"] = ite.fecha_pedido.dt.strftime("%Y-%m")
    meses = pd.period_range(INICIO, FIN, freq="M").strftime("%Y-%m")
    idx = pd.MultiIndex.from_product([t["productos"].producto_id, meses], names=["producto_id", "mes"])
    p = ite.groupby(["producto_id", "mes"]).agg(ventas=("importe", "sum"), unidades=("cantidad", "sum")).reindex(idx, fill_value=0).reset_index()
    g = p.groupby("producto_id").ventas
    for k in (1, 2, 3, 12): p[f"ventas_lag{k}"] = g.shift(k)
    p["ventas_media_3m"] = p[["ventas_lag1", "ventas_lag2", "ventas_lag3"]].mean(axis=1)
    p["ventas_media_historica"] = g.transform(lambda s: s.shift(1).expanding().mean())
    p["periodo"] = p.mes.map({m: i for i, m in enumerate(meses)}); p["mes_del_anio"] = p.mes.str[5:7].astype(int)
    dias = pd.date_range(INICIO, FIN, freq="D"); desc = _descuento_activo(t["campanias"], dias)
    cal = pd.DataFrame({"mes": desc.index.strftime("%Y-%m"), "d": desc.values, "act": (desc.values > 0)}).groupby("mes").agg(descuento_max=("d", "max"), dias_campania=("act", "sum"))
    p = p.merge(cal, on="mes", how="left")
    iv = t["inventario"][["producto_id", "mes", "stock_inicial", "quiebre_stock"]].sort_values(["producto_id", "mes"]).copy()
    iv["quiebre_lag1"] = iv.groupby("producto_id").quiebre_stock.shift(1).astype(float)
    p = p.merge(iv.drop(columns="quiebre_stock"), on=["producto_id", "mes"], how="left")
    ped = t["pedidos_integrados"]; ped = ped[ped.pedido_valido]
    cli = ped.groupby(ped.fecha_pedido.dt.strftime("%Y-%m").rename("mes")).cliente_id.nunique().reindex(meses).shift(1).rename("compradores_lag1")
    ses = t["navegacion"].groupby("mes").sesiones.sum().reindex(meses).shift(1).rename("sesiones_lag1")
    p = p.merge(cli, left_on="mes", right_index=True, how="left").merge(ses, left_on="mes", right_index=True, how="left")
    return p.merge(t["productos"][["producto_id", "categoria", "subcategoria", "marca", "precio_lista", "costo"]], on="producto_id", how="left")


def construir(t: dict[str, pd.DataFrame] | None = None) -> dict[str, pd.DataFrame]:
    t = t or cargar_procesados()
    return {"clientes_variables": agregar_rfm_clv(variables_cliente(t, CORTE_FINAL), retencion_anual(t, CORTE_FINAL)), "abandono_dataset": dataset_abandono(t),
            "productos_abc_xyz": abc_xyz(t), "serie_diaria": serie_diaria(t), "panel_producto_mes": panel_producto_mes(t)}


def main() -> dict[str, pd.DataFrame]:
    salida = construir()
    for n, df in salida.items():
        df.to_csv(PROCESSED / f"{n}.csv", index=False)
        print(f"{n:22s} {df.shape}")
    return salida


if __name__ == "__main__":
    main()
