"""EDA y diagnóstico de calidad de datos - SportSmart Perú. Salida: reports/eda.json (en la raíz del repo)"""
import pandas as pd, numpy as np, json, os
B=os.path.abspath(os.path.join(os.path.dirname(__file__),"..",".."))  # raíz del repo
R=os.path.join(B,"data","raw")
t={f[:-4]:pd.read_csv(os.path.join(R,f)) for f in sorted(os.listdir(R))}
out={}

# ---------- Inventario ----------
out["inventario"]={k:{"filas":int(v.shape[0]),"columnas":int(v.shape[1])} for k,v in t.items()}
out["total_registros"]=int(sum(v.shape[0] for v in t.values()))

# ---------- Calidad ----------
cal={}
for k,v in t.items():
    vv=v.replace(r"^\s*$",np.nan,regex=True)
    nul=vv.isna().sum(); nul=nul[nul>0]
    cal[k]={"nulos":{c:int(n) for c,n in nul.items()},
            "pct_celdas_nulas":round(100*vv.isna().sum().sum()/vv.size,2),
            "duplicados_exactos":int(v.duplicated().sum())}
c=t["clientes"]
cal["clientes"]["ids_duplicados"]=int(c.cliente_id.duplicated().sum())
cal["clientes"]["edad_fuera_rango"]=int(((c.edad<16)|(c.edad>90)).sum())
cal["clientes"]["genero_valores_distintos"]=sorted(c.genero.dropna().unique().tolist())
cal["clientes"]["genero_no_estandar"]=int((~c.genero.isin(["M","F"])&c.genero.notna()).sum())
dept_ok={"Lima","Arequipa","La Libertad","Piura","Lambayeque","Cusco","Junín","Ica","Áncash","Callao","Puno","Loreto"}
cal["clientes"]["departamento_mal_escrito"]=int((~c.departamento.isin(dept_ok)).sum())
cal["clientes"]["ejemplos_departamento"]=sorted(c.departamento[~c.departamento.isin(dept_ok)].unique().tolist())[:8]
d=t["detalle_pedido"]
cal["detalle_pedido"]["cantidad_no_positiva"]=int((d.cantidad<=0).sum())
cal["detalle_pedido"]["cantidad_atipica_mayor_10"]=int((d.cantidad>10).sum())  # IQR=0 en variable discreta -> regla de negocio
cal["detalle_pedido"]["cantidad_max"]=int(d.cantidad.max())
p=t["pedidos"]; p["fecha_pedido"]=pd.to_datetime(p.fecha_pedido)
cal["pedidos"]["fechas_futuras"]=int((p.fecha_pedido>pd.Timestamp("2026-10-12")).sum())
pg=t["pagos"].merge(p[["pedido_id","monto_total"]],on="pedido_id")
cal["pagos"]["importe_no_cuadra"]=int(((pg.importe-pg.monto_total).abs()>0.05).sum())
lg=t["logistica"]
cal["logistica"]["distancia_negativa"]=int((lg.distancia_km<0).sum())
de=lg.dias_entrega.dropna(); z=(de-de.mean())/de.std()
cal["logistica"]["dias_entrega_outliers_z3"]=int((z.abs()>3).sum())
o=t["opiniones"]
cal["opiniones"]["puntuacion_fuera_1_5"]=int((~o.puntuacion.between(1,5)).sum())
cal["opiniones"]["comentario_vacio"]=int(o.comentario.fillna("").str.strip().eq("").sum())
a=t["atencion"]; cal["atencion"]["horas_negativas"]=int((a.horas_resolucion<0).sum())
pr=t["productos"]; cal["productos"]["precio_nulo"]=int(pr.precio_lista.isna().sum())
out["calidad"]=cal

# ---------- EDA (sobre registros válidos) ----------
pv=p[(p.fecha_pedido<=pd.Timestamp("2026-09-30"))&(p.estado!="Cancelado")&p.monto_total.notna()].copy()
eda={}
eda["periodo"]=[str(pv.fecha_pedido.min().date()),str(pv.fecha_pedido.max().date())]
eda["pedidos_validos"]=int(len(pv)); eda["clientes_con_compra"]=int(pv.cliente_id.nunique())
eda["ventas_totales_soles"]=round(float(pv.monto_total.sum()),0)
eda["ticket_promedio"]=round(float(pv.monto_total.mean()),2)
eda["ticket_mediana"]=round(float(pv.monto_total.median()),2)
m=pv.set_index("fecha_pedido").monto_total.resample("MS").sum()
eda["ventas_mensuales"]={str(k.date())[:7]:round(float(v),0) for k,v in m.items()}
pa=pv.assign(a=pv.fecha_pedido.dt.year).groupby("a").monto_total.sum()
eda["ventas_anuales"]={int(k):round(float(v),0) for k,v in pa.items()}
cma=m.rolling(12,center=True).mean(); ratio=(m/cma).dropna()
mes=ratio.groupby(ratio.index.month).mean(); mes=mes/mes.mean()
eda["indice_estacional_mes"]={int(k):round(float(v),2) for k,v in mes.items()}
dd=d[(d.cantidad>0)&(d.cantidad<20)].drop_duplicates().merge(pr[["producto_id","categoria","subcategoria"]],on="producto_id")
dd=dd[dd.pedido_id.isin(pv.pedido_id)]
cat=dd.groupby("categoria").importe.sum().sort_values(ascending=False)
eda["ventas_categoria_pct"]={k:round(100*v/cat.sum(),1) for k,v in cat.items()}
eda["items_por_pedido"]=round(float(dd.groupby("pedido_id").size().mean()),2)
eda["pct_pedidos_multi_item"]=round(100*float((dd.groupby("pedido_id").size()>1).mean()),1)
# frecuencia de compra
f=pv.groupby("cliente_id").size()
eda["pedidos_por_cliente"]={"media":round(float(f.mean()),2),"mediana":float(f.median()),"p90":float(f.quantile(.9)),
  "pct_una_sola_compra":round(100*float((f==1).mean()),1)}
# recencia al cierre
rec=(pd.Timestamp("2026-09-30")-pv.groupby("cliente_id").fecha_pedido.max()).dt.days
eda["pct_clientes_sin_compra_180d"]=round(100*float((rec>180).mean()),1)
# concentración de ventas (Pareto)
mc=pv.groupby("cliente_id").monto_total.sum().sort_values(ascending=False)
eda["pct_ventas_top20_clientes"]=round(100*float(mc.head(int(len(mc)*.2)).sum()/mc.sum()),1)
# geografía
cl=c.drop_duplicates("cliente_id")
dep=cl.departamento.str.strip().str.title().replace({"Junin":"Junín","Ancash":"Áncash","Cuzco":"Cusco","La Libertad":"La Libertad"})
cl=cl.assign(dep=dep)
g=pv.merge(cl[["cliente_id","dep"]],on="cliente_id").groupby("dep").monto_total.sum().sort_values(ascending=False)
eda["ventas_departamento_pct"]={k:round(100*v/g.sum(),1) for k,v in g.head(8).items()}
# demografía
e=cl.edad[(cl.edad>=16)&(cl.edad<=90)]
eda["edad"]={"media":round(float(e.mean()),1),"mediana":float(e.median()),"p25":float(e.quantile(.25)),"p75":float(e.quantile(.75))}
eda["deporte_preferido_pct"]={k:round(100*v,1) for k,v in cl.deporte_preferido.value_counts(normalize=True).items()}
# pagos
pgv=t["pagos"][t["pagos"].pedido_id.isin(pv.pedido_id)]
eda["metodo_pago_pct"]={k:round(100*v,1) for k,v in pgv.metodo.value_counts(normalize=True).items()}
# devoluciones
dv=t["devoluciones"]
ent_items=dd.merge(p[["pedido_id","estado"]],on="pedido_id"); ent_items=ent_items[ent_items.estado=="Entregado"]
tasa=dv.merge(pr[["producto_id","categoria"]],on="producto_id").groupby("categoria").size()/ent_items.groupby("categoria").size()
eda["tasa_devolucion_categoria_pct"]={k:round(100*v,1) for k,v in tasa.sort_values(ascending=False).items()}
eda["tasa_devolucion_global_pct"]=round(100*len(dv)/len(ent_items),1)
eda["motivo_devolucion_pct"]={k:round(100*v,1) for k,v in dv.motivo.value_counts(normalize=True).items()}
# logística
lgv=lg[(lg.distancia_km>0)&lg.dias_entrega.between(0,40)]
lgv=lgv.merge(p[["pedido_id","cliente_id"]],on="pedido_id").merge(cl[["cliente_id","dep"]],on="cliente_id")
lgv["zona"]=np.where(lgv.dep.isin(["Lima","Callao"]),"Lima/Callao","Provincias")
eda["entrega"]={z:{"dias_prom":round(float(g.dias_entrega.mean()),1),"pct_a_tiempo":round(100*float(g.entrega_a_tiempo.astype(str).eq("True").mean()),1)} for z,g in lgv.groupby("zona")}
# opiniones
ov=o[o.puntuacion.between(1,5)]
eda["puntuacion_dist_pct"]={int(k):round(100*v,1) for k,v in ov.puntuacion.value_counts(normalize=True).sort_index().items()}
eda["puntuacion_media"]=round(float(ov.puntuacion.mean()),2)
lt=ov.merge(lg[["pedido_id","entrega_a_tiempo"]],on="pedido_id")
eda["puntuacion_media_por_entrega"]={"a_tiempo":round(float(lt[lt.entrega_a_tiempo.astype(str)=="True"].puntuacion.mean()),2),
   "con_retraso":round(float(lt[lt.entrega_a_tiempo.astype(str)=="False"].puntuacion.mean()),2)}
# atención
av=a[a.horas_resolucion>=0]
eda["atencion"]={"tickets":int(len(a)),"pct_reclamos":round(100*float((a.tipo=="Reclamo").mean()),1),
  "horas_mediana":float(av.horas_resolucion.median()),"tema_top":a.tema.value_counts(normalize=True).round(3).mul(100).to_dict()}
# marketing
mk=t["marketing"]; eda["marketing"]={"tasa_apertura":round(100*float(mk.abrio.mean()),1),"ctr":round(100*float(mk.hizo_clic.mean()),1)}
eda["pct_pedidos_con_campania"]=round(100*float(pv.campania_id.notna().mean()),1)
# navegación
nv=t["navegacion"]; eda["navegacion"]={"sesiones_mes_media":round(float(nv.sesiones.mean()),2),
  "pct_sesiones_con_carrito_abandonado":round(100*float(nv.carritos_abandonados.sum()/nv.sesiones.sum()),1),
  "dispositivo_pct":{k:round(100*v,1) for k,v in nv.dispositivo.value_counts(normalize=True).items()}}
# top pares de subcategorías (vista previa de asociación)
from itertools import combinations
from collections import Counter
cnt=Counter(); sub_cnt=dd.drop_duplicates(["pedido_id","subcategoria"]).groupby("subcategoria").size()
for _,s in dd.drop_duplicates(["pedido_id","subcategoria"]).groupby("pedido_id").subcategoria:
    for a_,b_ in combinations(sorted(s),2): cnt[(a_,b_)]+=1
N=dd.pedido_id.nunique()
pares=[]
for (a_,b_),n in cnt.most_common(6):
    sup=n/N; lift=sup/((sub_cnt[a_]/N)*(sub_cnt[b_]/N))
    pares.append({"par":f"{a_} + {b_}","soporte_pct":round(100*sup,2),"lift":round(lift,2)})
eda["top_pares"]=pares
out["eda"]=eda
os.makedirs(os.path.join(B,"reports"),exist_ok=True)
json.dump(out,open(os.path.join(B,"reports","eda.json"),"w"),ensure_ascii=False,indent=1)
print(json.dumps(out,ensure_ascii=False,indent=1))
