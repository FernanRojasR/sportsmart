"""Primer prototipo del dashboard de SportSmart. Ejecutar:  streamlit run frontend/app.py"""
import altair as alt
import pandas as pd
import streamlit as st

import datos
from src.data.estilo_graficos import AGUA, AZUL, GRIS, NARANJA, numero

st.set_page_config(page_title="SportSmart Analytics", page_icon="📊", layout="wide")

SOLES = lambda v: f"S/ {numero(v, 0)}"
PCT = lambda v, d=1: f"{numero(v, d)} %"
COLOR_SEGMENTO = {"Alto valor activos": AZUL, "Valiosos inactivos": NARANJA, "Ocasionales inactivos": AGUA}


@st.cache_data
def cargar() -> dict:
    return {
        "clustering": datos.leer_json("clustering"), "series": datos.leer_json("series"), "regresion": datos.leer_json("regresion"), "grafos": datos.leer_json("grafos"), "asociacion": datos.leer_json("asociacion"),
        "evaluacion": datos.leer_json("evaluacion"), "preparacion": datos.leer_json("preparacion"), "caracteristicas": datos.leer_json("caracteristicas"),
        "reglas": datos.leer_reporte_csv("reglas_asociacion"), "pronostico": datos.leer_reporte_csv("pronostico_ventas", parse_dates=["fecha"]), "predicciones": datos.leer_reporte_csv("predicciones_regresion"), "nodos": datos.leer_reporte_csv("grafo_productos"), "segmentos": datos.leer_segmentos(),
    }


def tabla(df: pd.DataFrame) -> None:
    st.dataframe(df, hide_index=True, width="stretch")


def grafico(c: alt.Chart) -> None:
    st.altair_chart(c.configure_view(strokeWidth=0).configure_axis(grid=False, labelFontSize=12, titleFontSize=12, domainColor="#c3c2b7", tickColor="#c3c2b7"), theme=None, width="stretch")


def barras(df: pd.DataFrame, cat: str, val: str, etiqueta: str, altura: int = 260, resaltar: str | None = None, colores: dict | None = None) -> None:
    color = alt.Color(f"{cat}:N", scale=alt.Scale(domain=list(colores), range=list(colores.values())), legend=None) if colores else (alt.condition(alt.datum[cat] == resaltar, alt.value(NARANJA), alt.value(AZUL)) if resaltar else alt.value(AZUL))
    y = alt.Y(f"{cat}:N", sort=None, title=None, axis=alt.Axis(labelLimit=260))
    b = alt.Chart(df).mark_bar(cornerRadiusEnd=3, height=22).encode(x=alt.X(f"{val}:Q", title=None, axis=None), y=y, color=color, tooltip=[alt.Tooltip(f"{cat}:N", title="Elemento"), alt.Tooltip(f"{etiqueta}:N", title="Valor")])
    t = alt.Chart(df).mark_text(align="left", dx=4, fontSize=12, color="#0b0b0b").encode(x=f"{val}:Q", y=y, text=f"{etiqueta}:N")
    grafico((b + t).properties(height=altura))


def valor_tecnica(tecnica: str, v: float) -> str:
    if tecnica == "Asociación":
        return numero(v, 0)
    return numero(v, 2 if tecnica == "Series temporales" else 3)


def textos(df: pd.DataFrame) -> None:
    """Tabla que ajusta el texto largo en vez de truncarlo."""
    st.table(df.set_index(df.columns[0]))


def aviso() -> None:
    st.caption("Datos simulados con fines académicos. Prototipo de las semanas 10 y 13; la aplicación final se presenta en la semana 16.")


def pagina_resumen(d: dict) -> None:
    st.title("SportSmart Analytics")
    st.write("Resumen de las técnicas de minería de datos sobre clientes, productos y ventas.")
    v, f = d["preparacion"]["ventas_validas"], datos.resumen_horizonte(d["series"], 90)
    a, b, c, e = st.columns(4)
    a.metric("Ventas válidas", SOLES(v["soles_despues"])); b.metric("Pedidos válidos", numero(v["pedidos_despues"], 0)); c.metric("Compradores", numero(d["clustering"]["clientes"], 0))
    e.metric("Pronóstico a 90 días", SOLES(f["pronostico"]), f"{numero(f['variacion_pct'])} % frente al año anterior")
    st.subheader("Evolución de las ventas")
    m = pd.DataFrame({"mes": list(d["series"]["ventas_mensuales"]), "ventas": [x / 1000 for x in d["series"]["ventas_mensuales"].values()]})
    m["etiqueta"] = m.ventas.map(lambda x: f"S/ {numero(x, 0)} mil")
    grafico(alt.Chart(m).mark_line(color=AZUL, strokeWidth=2).encode(x=alt.X("mes:O", title=None, axis=alt.Axis(labelAngle=-45, values=list(m.mes[::6]))), y=alt.Y("ventas:Q", title="Miles de S/"), tooltip=[alt.Tooltip("mes:O", title="Mes"), alt.Tooltip("etiqueta:N", title="Ventas")]).properties(height=280))
    st.subheader("Resultados por técnica")
    filas = [{"Técnica": r["tecnica"], "Modelo": r["modelo"], "Métrica": r["metrica"], "Resultado": valor_tecnica(r["tecnica"], r["resultado"]), "Meta": r["meta"], "¿Cumple?": "Sí" if r["cumple"] else "No"} for r in d["evaluacion"]["resultados"]]
    tabla(pd.DataFrame(filas))


def pagina_segmentos(d: dict) -> None:
    st.title("Segmentación de clientes")
    c = d["clustering"]; p = pd.DataFrame(c["perfil_segmentos"])
    st.write(f"K-Means sobre RFM, con silhouette de {numero(c['comparacion']['K-Means RFM (k=3)']['silhouette'], 3)}.")
    for col, (_, s) in zip(st.columns(3), p.iterrows()):
        col.metric(s.segmento, f"{numero(s.clientes, 0)} compradores", f"{PCT(s.pct_ventas)} de las ventas históricas", delta_color="off", delta_arrow="off")
    izq, der = st.columns(2)
    with izq:
        st.subheader("Participación en ventas")
        barras(p.assign(e=p.pct_ventas.map(PCT)), "segmento", "pct_ventas", "e", 180, colores=COLOR_SEGMENTO)
        tabla(p[["segmento", "recencia", "frecuencia", "monetario", "clv"]].rename(columns={"segmento": "Segmento", "recencia": "Días sin comprar", "frecuencia": "Pedidos", "monetario": "Gasto (S/)", "clv": "CLV (S/)"}).round(0))
        st.caption("Valores medianos por segmento.")
    with der:
        st.subheader("Mapa de segmentos")
        xy = pd.DataFrame({k: c["pca"][k] for k in ("x", "y", "segmento")})
        grafico(alt.Chart(xy).mark_circle(size=16, opacity=.65).encode(x=alt.X("x:Q", title="Componente 1"), y=alt.Y("y:Q", title="Componente 2"), color=alt.Color("segmento:N", title=None, scale=alt.Scale(domain=list(COLOR_SEGMENTO), range=list(COLOR_SEGMENTO.values())), legend=alt.Legend(orient="top")), tooltip=[alt.Tooltip("segmento:N", title="Segmento")]).properties(height=340))
    st.subheader("Consultar un cliente")
    if d["segmentos"] is None:
        st.info("Para consultar clientes, ejecuta primero: python -m src.pipeline --sin-datos")
        return
    cid = st.text_input("Código de cliente", "C00001", help="Por ejemplo, C00001")
    r = datos.buscar_cliente(d["segmentos"], cid)
    if r is None:
        st.warning("Ese código no corresponde a un comprador con pedidos válidos.")
    else:
        a, b, e, f = st.columns(4)
        a.metric("Segmento", r.segmento); b.metric("Días sin comprar", numero(r.recencia, 0)); e.metric("Pedidos", numero(r.frecuencia, 0)); f.metric("CLV estimado", SOLES(r.clv))
        if r.atipico_dbscan:
            st.info("Cliente atípico según DBSCAN: su comportamiento se aparta mucho del resto.")


def pagina_asociacion(d: dict) -> None:
    st.title("Reglas de asociación")
    a = d["asociacion"]["reglas"]; x, y, z = st.columns(3)
    x.metric("Reglas encontradas", a["total"]); y.metric("No redundantes", a["no_redundantes"]); z.metric("Lift máximo", numero(a["lift_max"], 2))
    st.subheader("¿Qué ofrecer junto a una subcategoría?")
    i, j = st.columns([2, 1]); opciones = datos.subcategorias_con_reglas(d["reglas"])
    sub = i.selectbox("Subcategoría comprada", opciones, index=opciones.index("Casaca cortaviento")); lift = j.slider("Lift mínimo", 1.5, 6.0, 1.5, .5)
    r = datos.recomendaciones(d["reglas"], sub, lift)
    if r.empty:
        st.info("No hay reglas con ese lift para esta subcategoría.")
    else:
        barras(r.assign(e=r.lift.map(lambda v: numero(v, 2))), "consecuente", "lift", "e", 40 * len(r) + 30)
        tabla(r.assign(soporte=r.soporte.map(lambda v: PCT(100 * v, 2)), confianza=r.confianza.map(lambda v: PCT(100 * v)), lift=r.lift.map(lambda v: numero(v, 2))).rename(columns=str.capitalize))
    st.subheader("Todas las reglas no redundantes")
    t = d["reglas"]; t = t[~t.redundante]
    tabla(pd.DataFrame({"Antecedente": t.antecedente, "Consecuente": t.consecuente, "Soporte": t.soporte.map(lambda v: PCT(100 * v, 2)), "Confianza": t.confianza.map(lambda v: PCT(100 * v)), "Lift": t.lift.map(lambda v: numero(v, 2))}))


def pagina_pronostico(d: dict) -> None:
    st.title("Pronóstico de ventas")
    s = d["series"]; h = st.segmented_control("Horizonte (días)", datos.HORIZONTES, default=90) or 90
    f = datos.resumen_horizonte(s, h); a, b, c = st.columns(3)
    a.metric(f"Ventas esperadas en {h} días", SOLES(f["pronostico"]), f"{numero(f['variacion_pct'])} % frente al año anterior")
    b.metric("Rango de 80 % (miles de S/)", f"{numero(f['limite_inferior_80'] / 1000, 0)} a {numero(f['limite_superior_80'] / 1000, 0)}"); c.metric("MAPE semanal en prueba", PCT(s["prueba_6_meses"]["Prophet"]["mape_semanal"], 2))
    t = datos.pronostico_hasta(d["pronostico"], h).assign(p=lambda x: x.pronostico / 1000, i=lambda x: x.limite_inferior / 1000, u=lambda x: x.limite_superior / 1000, e=lambda x: x.pronostico.map(SOLES))
    x = alt.X("fecha:T", title=None, axis=alt.Axis(format="%d/%m"))
    banda = alt.Chart(t).mark_area(color=AZUL, opacity=.18).encode(x=x, y=alt.Y("i:Q", title="Miles de S/ por día"), y2="u:Q")
    linea = alt.Chart(t).mark_line(color=AZUL, strokeWidth=2).encode(x=x, y="p:Q", tooltip=[alt.Tooltip("fecha:T", title="Fecha", format="%d/%m/%Y"), alt.Tooltip("e:N", title="Pronóstico")])
    grafico((banda + linea).properties(height=320))
    st.caption(s["supuesto_campanias"] + " El modelo sirve para planificar por semana o periodo: el MAPE diario es de " + PCT(s["prueba_6_meses"]["Prophet"]["mape_diario"], 2) + ".")
    st.subheader("Comparación de modelos")
    m = pd.DataFrame(s["prueba_6_meses"]).T.reset_index(names="Modelo")[["Modelo", "mape_semanal", "mape_diario"]].sort_values("mape_semanal")
    tabla(pd.DataFrame({"Modelo": m.Modelo, "MAPE semanal (%)": m.mape_semanal.map(lambda v: numero(v, 2)), "MAPE diario (%)": m.mape_diario.map(lambda v: numero(v, 2))}))


def pagina_regresion(d: dict) -> None:
    st.title("Regresión de ventas")
    v = d["regresion"]["ventas"]; mv = v["modelos"][v["mejor_modelo"]]; a, b, c = st.columns(3)
    a.metric("Modelo", v["mejor_modelo"]); b.metric("R² en prueba", numero(mv["r2"], 3)); c.metric("Error total mensual", PCT(v["total_mensual"]["wape_pct"]))
    p = d["predicciones"]; i, j = st.columns(2); cat = i.selectbox("Categoría", ["Todas", *sorted(p.categoria.unique())]); pool = p if cat == "Todas" else p[p.categoria == cat]
    prod = j.selectbox("Producto", ["Todos", *sorted(pool.producto_id.unique())])
    t = datos.real_vs_prediccion(p, None if cat == "Todas" else cat, None if prod == "Todos" else prod).melt("mes", var_name="serie", value_name="soles")
    t["serie"] = t.serie.map({"ventas": "Ventas reales", "prediccion": "Predicción"}); t["e"] = t.soles.map(SOLES); t["miles"] = t.soles / 1000
    grafico(alt.Chart(t).mark_line(strokeWidth=2, point=True).encode(x=alt.X("mes:O", title=None, axis=alt.Axis(labelAngle=0)), y=alt.Y("miles:Q", title="Miles de S/", scale=alt.Scale(zero=True)), color=alt.Color("serie:N", title=None, scale=alt.Scale(domain=["Ventas reales", "Predicción"], range=[AZUL, NARANJA]), legend=alt.Legend(orient="top")), tooltip=[alt.Tooltip("mes:O", title="Mes"), alt.Tooltip("serie:N", title="Serie"), alt.Tooltip("e:N", title="Valor")]).properties(height=300))
    st.subheader("Factores que explican las ventas")
    b_ = pd.DataFrame({"factor": list(v["importancia_bloques"]), "caida": list(v["importancia_bloques"].values())}); b_["e"] = b_.caida.map(lambda x: numero(x, 3))
    barras(b_, "factor", "caida", "e", 260, resaltar=b_.factor.iloc[0])
    st.caption("Caída del R² al barajar cada grupo de variables.")


def pagina_grafos(d: dict) -> None:
    st.title("Relaciones y comunidades")
    g = d["grafos"]; co = g["comunidades"]; a, b, c = st.columns(3)
    a.metric("Modularidad", numero(co["modularidad"], 3), f"{numero(co['referencia_azar']['modularidad_media'], 3)} con compras al azar", delta_color="off", delta_arrow="off"); b.metric("Comunidades", co["n"]); c.metric("Aristas de compra", numero(g["heterogeneo"]["aristas_compra"], 0))
    st.image(str(datos.figura("grafo_subcategorias")), width="stretch")
    st.subheader("Productos más centrales por comunidad")
    nombre = st.selectbox("Comunidad", list(datos.COMUNIDADES.values())); idx = next(k for k, v in datos.COMUNIDADES.items() if v == nombre)
    tabla(datos.productos_comunidad(d["nodos"], idx).assign(pagerank=lambda x: x.pagerank.map(lambda v: numero(v, 4))).rename(columns=str.capitalize))


def pagina_evaluacion(d: dict) -> None:
    st.title("Evaluación comparativa")
    e = d["evaluacion"]
    filas = [{"Técnica": r["tecnica"], "Modelo": r["modelo"], "Resultado": valor_tecnica(r["tecnica"], r["resultado"]), "Meta": r["meta"], "Referencia simple": r["referencia_nombre"], "Valor de referencia": valor_tecnica(r["tecnica"], r["referencia"]), "¿La supera?": "Sí" if r["supera_referencia"] else "No"} for r in e["resultados"]]
    tabla(pd.DataFrame(filas))
    st.subheader("Resultados que no alcanzan lo esperado")
    textos(pd.DataFrame(e["no_alcanzadas"]).rename(columns={"analisis": "Análisis", "resultado": "Resultado", "referencia_meta": "Esperado", "causa": "Causa", "decision": "Decisión"}))
    st.subheader("Respuestas a las preguntas de negocio")
    textos(pd.DataFrame(e["respuestas"]).drop(columns="n").rename(columns={"pregunta": "Pregunta", "respuesta": "Respuesta"}))


PAGINAS = {"Resumen": pagina_resumen, "Segmentación": pagina_segmentos, "Asociación": pagina_asociacion, "Pronóstico": pagina_pronostico, "Regresión": pagina_regresion, "Grafos": pagina_grafos, "Evaluación": pagina_evaluacion}


def main() -> None:
    d = cargar()
    with st.sidebar:
        st.header("SportSmart Analytics")
        pagina = st.radio("Sección", list(PAGINAS), label_visibility="collapsed")
        st.divider()
        st.caption("Próximamente, en la semana 16: clasificación, minería de textos, explicabilidad y monitoreo.")
    PAGINAS[pagina](d)
    st.divider(); aviso()


main()
