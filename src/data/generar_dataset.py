"""Generador del dataset sintético SportSmart Perú (e-commerce de ropa deportiva).
Incluye problemas de calidad intencionales para la fase de Comprensión de los Datos.
Semilla fija -> reproducible.
"""
import numpy as np, pandas as pd, os
rng = np.random.default_rng(42)
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))  # raíz del repo
OUT = os.path.join(ROOT, "data", "raw")
os.makedirs(OUT, exist_ok=True)

INI, FIN = pd.Timestamp("2023-01-01"), pd.Timestamp("2026-09-30")
dias = pd.date_range(INI, FIN, freq="D")

# ---------------- CLIENTES ----------------
N_CLI = 15000
deptos = ["Lima","Arequipa","La Libertad","Piura","Lambayeque","Cusco","Junín","Ica","Áncash","Callao","Puno","Loreto"]
p_dep = np.array([.48,.08,.07,.05,.05,.05,.05,.04,.03,.06,.02,.02]); p_dep/=p_dep.sum()
n_old = int(N_CLI*.25)   # base de clientes previa a 2023
reg = np.concatenate([pd.Timestamp("2021-03-01").value + rng.integers(0,(INI-pd.Timestamp("2021-03-01")).days,n_old)*86400*10**9,
                      INI.value + rng.integers(0,(FIN-INI).days-30,N_CLI-n_old)*86400*10**9])
reg = pd.to_datetime(np.sort(reg))
edad = np.clip(rng.normal(31,9,N_CLI).round(),16,70).astype(float)
clientes = pd.DataFrame({
  "cliente_id": [f"C{i:05d}" for i in range(1,N_CLI+1)],
  "edad": edad,
  "genero": rng.choice(["M","F"],N_CLI,p=[.54,.46]),
  "departamento": rng.choice(deptos,N_CLI,p=p_dep),
  "fecha_registro": reg,
  "canal_adquisicion": rng.choice(["Orgánico","Facebook/Instagram","Google Ads","TikTok","Referido"],N_CLI,p=[.3,.25,.2,.15,.1]),
  "deporte_preferido": rng.choice(["Running","Training","Fútbol","Outdoor","Yoga","Ciclismo"],N_CLI,p=[.28,.27,.2,.1,.08,.07]),
})
# perfil latente de actividad (no se exporta)
actividad = rng.gamma(0.5,1.0,N_CLI)
# vida útil del cliente (abandono latente): muchos dejan de comprar
vida_dias = rng.exponential(420,N_CLI)
fin_vida = reg + pd.to_timedelta(vida_dias,"D")

# ---------------- PRODUCTOS ----------------
cats = {
 "Calzado":[("Zapatillas running",(189,549)),("Zapatillas training",(169,449)),("Chimpunes",(149,499)),("Sandalias",(59,149))],
 "Ropa superior":[("Polo dry-fit",(49,129)),("Casaca cortaviento",(149,349)),("Top deportivo",(59,139)),("Polera",(119,259))],
 "Ropa inferior":[("Short",(49,119)),("Licra",(69,169)),("Jogger",(99,219))],
 "Accesorios":[("Medias",(19,49)),("Tomatodo",(29,89)),("Gorra",(39,99)),("Mochila",(99,259)),("Muñequera",(15,39))],
 "Equipamiento":[("Pelota",(59,199)),("Mat de yoga",(69,179)),("Mancuernas",(49,249)),("Banda elástica",(29,79))],
}
marcas = ["Nike","Adidas","Puma","Under Armour","New Balance","Reebok","Marca propia"]
rows=[]; pid=1
for cat,subs in cats.items():
    for sub,(lo,hi) in subs:
        for _ in range(rng.integers(12,20)):
            precio = float(round(rng.uniform(lo,hi))-0.1)
            rows.append(dict(producto_id=f"P{pid:04d}",nombre=f"{sub} {rng.choice(['Pro','Air','Flex','Core','Elite','Max','Lite'])} {pid}",
                categoria=cat,subcategoria=sub,marca=rng.choice(marcas,p=[.22,.2,.12,.1,.1,.08,.18]),
                precio_lista=precio,costo=round(precio*rng.uniform(.45,.6),2),
                talla_aplica= cat in ("Calzado","Ropa superior","Ropa inferior")))
            pid+=1
productos=pd.DataFrame(rows)
sub_idx={s:productos.index[productos.subcategoria==s].values for s in productos.subcategoria.unique()}

# ---------------- PEDIDOS + DETALLE ----------------
def factor_estacional(d):
    f=1.0
    f*= {1:1.35,2:1.05,3:1.15,4:.9,5:.95,6:.9,7:1.2,8:.95,9:.95,10:1.0,11:1.45,12:1.6}[d.month]
    if d.day in (15,16,30,31,1): f*=1.25           # quincenas
    if d.weekday()>=5: f*=1.15
    return f
trend = np.linspace(1.0,1.6,len(dias))
lam = np.array([factor_estacional(d) for d in dias])*trend*30
n_ped_dia = rng.poisson(lam)
# asignar cada pedido a un cliente registrado y aún activo ese día (prob ~ actividad)
reg_v, fin_v = reg.values, fin_vida.values
fechas_l, cli_l = [], []
for d, n in zip(dias.values, n_ped_dia):
    if n == 0: continue
    elig = np.where((reg_v <= d) & (fin_v >= d))[0]
    w = actividad[elig]; sel = rng.choice(elig, n, p=w/w.sum())
    fechas_l.append(np.repeat(d, n)); cli_l.append(sel)
fechas_ped = np.concatenate(fechas_l); cli_choice = np.concatenate(cli_l)
NP=len(fechas_ped)
pedidos = pd.DataFrame({"pedido_id":[f"O{i:06d}" for i in range(1,NP+1)],
    "cliente_id":clientes.cliente_id.values[cli_choice],
    "fecha_pedido":pd.to_datetime(fechas_ped)+pd.to_timedelta(rng.integers(0,86400,NP),"s"),
    "campania_id":None})
pedidos=pedidos.sort_values("fecha_pedido").reset_index(drop=True)
pedidos["pedido_id"]=[f"O{i:06d}" for i in range(1,NP+1)]
dep_pref=clientes.set_index("cliente_id").deporte_preferido

# canastas con reglas latentes
reglas={"Zapatillas running":["Medias","Short","Tomatodo","Polo dry-fit"],
        "Chimpunes":["Medias","Pelota","Short"],"Zapatillas training":["Licra","Top deportivo","Banda elástica","Tomatodo"],
        "Mat de yoga":["Licra","Top deportivo","Banda elástica"],"Casaca cortaviento":["Mochila","Gorra","Jogger"]}
inicio_por_dep={"Running":["Zapatillas running","Polo dry-fit","Short","Medias"],"Training":["Zapatillas training","Licra","Mancuernas","Top deportivo"],
  "Fútbol":["Chimpunes","Pelota","Short","Medias"],"Outdoor":["Casaca cortaviento","Mochila","Polera","Gorra"],
  "Yoga":["Mat de yoga","Licra","Top deportivo","Muñequera"],"Ciclismo":["Polo dry-fit","Licra","Tomatodo","Gorra"]}
det=[]
deps=dep_pref.loc[pedidos.cliente_id].values
for i,(oid,dp) in enumerate(zip(pedidos.pedido_id.values,deps)):
    base = inicio_por_dep[dp][rng.choice(4,p=[.4,.25,.2,.15])] if rng.random()<.75 else rng.choice(productos.subcategoria.unique())
    subs=[base]
    for s in reglas.get(base,[]):
        if rng.random()<.32: subs.append(s)
    if rng.random()<.25: subs.append(rng.choice(["Medias","Tomatodo","Gorra","Muñequera"]))
    for s in dict.fromkeys(subs):
        pi=rng.choice(sub_idx[s]); pr=productos.loc[pi]
        q=1 if pr.precio_lista>100 else int(rng.choice([1,2,3],p=[.7,.22,.08]))
        talla = rng.choice(["XS","S","M","L","XL"] if pr.categoria!="Calzado" else ["38","39","40","41","42","43"]) if pr.talla_aplica else None
        det.append((oid,pr.producto_id,q,pr.precio_lista,talla))
detalle=pd.DataFrame(det,columns=["pedido_id","producto_id","cantidad","precio_unitario","talla"])
# descuentos por campaña
camp_rows=[("CMP01","Verano Activo","2023-01-05","2023-01-31","Email",.15),("CMP02","Fiestas Patrias","2023-07-15","2023-07-31","Facebook/Instagram",.2),
 ("CMP03","Cyber Wow","2023-11-06","2023-11-09","Google Ads",.3),("CMP04","Black Friday","2023-11-24","2023-11-27","Facebook/Instagram",.35),
 ("CMP05","Navidad","2023-12-10","2023-12-24","Email",.15),("CMP06","Propósitos 2024","2024-01-02","2024-01-31","TikTok",.2),
 ("CMP07","Regreso a clases","2024-03-01","2024-03-20","Facebook/Instagram",.15),("CMP08","Fiestas Patrias","2024-07-15","2024-07-31","TikTok",.2),
 ("CMP09","Cyber Wow","2024-11-04","2024-11-07","Google Ads",.3),("CMP10","Black Friday","2024-11-29","2024-12-02","Facebook/Instagram",.35),
 ("CMP11","Navidad","2024-12-08","2024-12-24","Email",.15),("CMP12","Propósitos 2025","2025-01-02","2025-01-31","TikTok",.2),
 ("CMP13","Regreso a clases","2025-03-01","2025-03-20","Facebook/Instagram",.15),("CMP14","Fiestas Patrias","2025-07-15","2025-07-31","TikTok",.2),
 ("CMP15","Cyber Wow","2025-11-03","2025-11-06","Google Ads",.3),("CMP16","Black Friday","2025-11-28","2025-12-01","Facebook/Instagram",.35),
 ("CMP17","Navidad","2025-12-07","2025-12-24","Email",.15),("CMP18","Propósitos 2026","2026-01-02","2026-01-31","TikTok",.2),
 ("CMP19","Regreso a clases","2026-03-01","2026-03-20","Facebook/Instagram",.15),("CMP20","Fiestas Patrias","2026-07-15","2026-07-31","TikTok",.2)]
campanias=pd.DataFrame(camp_rows,columns=["campania_id","nombre","fecha_inicio","fecha_fin","canal","descuento"])
campanias[["fecha_inicio","fecha_fin"]]=campanias[["fecha_inicio","fecha_fin"]].apply(pd.to_datetime)
fd=pedidos.fecha_pedido.dt.normalize()
for c in campanias.itertuples():
    m=(fd>=c.fecha_inicio)&(fd<=c.fecha_fin)&(rng.random(NP)<.6)
    pedidos.loc[m,"campania_id"]=c.campania_id
desc=pedidos.campania_id.map(campanias.set_index("campania_id").descuento).fillna(0)
detalle["descuento"]=detalle.pedido_id.map(dict(zip(pedidos.pedido_id,desc)))
detalle["importe"]=(detalle.cantidad*detalle.precio_unitario*(1-detalle.descuento)).round(2)
tot=detalle.groupby("pedido_id").importe.sum()
pedidos["monto_total"]=pedidos.pedido_id.map(tot).round(2)
pedidos["estado"]=rng.choice(["Entregado","Cancelado","En tránsito"],NP,p=[.93,.05,.02])
pedidos.loc[pedidos.fecha_pedido<FIN-pd.Timedelta(days=10),"estado"]=pedidos.estado.replace("En tránsito","Entregado")

# ---------------- PAGOS ----------------
pagos=pd.DataFrame({"pago_id":[f"PG{i:06d}" for i in range(1,NP+1)],"pedido_id":pedidos.pedido_id,
  "metodo":rng.choice(["Tarjeta crédito","Tarjeta débito","Yape","Plin","PagoEfectivo","Contraentrega"],NP,p=[.32,.2,.25,.08,.08,.07]),
  "cuotas":1,"importe":pedidos.monto_total,"estado_pago":"Aprobado"})
cc=pagos.metodo=="Tarjeta crédito"; pagos.loc[cc,"cuotas"]=rng.choice([1,3,6,12],cc.sum(),p=[.55,.25,.12,.08])
pagos.loc[pedidos.estado=="Cancelado","estado_pago"]=rng.choice(["Rechazado","Reembolsado"],(pedidos.estado=="Cancelado").sum())

# ---------------- LOGÍSTICA ----------------
dpto=pedidos.cliente_id.map(clientes.set_index("cliente_id").departamento)
dist={"Lima":15,"Callao":20,"Ica":300,"Áncash":400,"Junín":300,"La Libertad":560,"Arequipa":1010,"Lambayeque":770,"Piura":980,"Cusco":1100,"Puno":1300,"Loreto":1850}
dk=dpto.map(dist).values*rng.uniform(.8,1.3,NP)
dias_ent=np.round(1+dk/350+rng.gamma(1.5,.8,NP)).astype(int)
ent=pedidos.estado=="Entregado"
logistica=pd.DataFrame({"envio_id":[f"E{i:06d}" for i in range(1,NP+1)],"pedido_id":pedidos.pedido_id,
 "operador":np.where(dpto.isin(["Lima","Callao"]),rng.choice(["Flota propia","Olva"],NP,p=[.6,.4]),rng.choice(["Olva","Shalom","Serpost"],NP,p=[.5,.35,.15])),
 "distancia_km":dk.round(1),"costo_envio":np.where(pedidos.monto_total>199,0,np.round(9.9+dk*0.012,1)),
 "fecha_envio":pedidos.fecha_pedido.dt.normalize()+pd.Timedelta(days=1),
 "dias_entrega":np.where(ent,dias_ent,np.nan),"dias_prometidos":np.where(dpto.isin(["Lima","Callao"]),3,6)})
logistica["entrega_a_tiempo"]=np.where(ent,logistica.dias_entrega<=logistica.dias_prometidos,None)

# ---------------- DEVOLUCIONES ----------------
dj=detalle.merge(productos[["producto_id","categoria","talla_aplica"]],on="producto_id")
dj=dj[dj.pedido_id.isin(pedidos.pedido_id[ent])]
p_dev=np.where(dj.categoria=="Calzado",.13,np.where(dj.talla_aplica,.09,.025))
md=rng.random(len(dj))<p_dev
dv=dj[md].copy()
motivos_talla=["Talla incorrecta","Talla incorrecta","Talla incorrecta","Producto defectuoso","No coincide con la foto","Cambio de opinión","Llegó tarde"]
motivos_ot=["Producto defectuoso","No coincide con la foto","Cambio de opinión","Llegó tarde"]
dv["motivo"]=[rng.choice(motivos_talla) if t else rng.choice(motivos_ot) for t in dv.talla_aplica]
fped=dict(zip(pedidos.pedido_id,pedidos.fecha_pedido))
dv["fecha_devolucion"]=dv.pedido_id.map(fped).dt.normalize()+pd.to_timedelta(rng.integers(5,30,len(dv)),"D")
devoluciones=dv[["pedido_id","producto_id","talla","motivo","fecha_devolucion"]].reset_index(drop=True)
devoluciones.insert(0,"devolucion_id",[f"D{i:05d}" for i in range(1,len(devoluciones)+1)])
devoluciones["monto_reembolso"]=dv.importe.values

# ---------------- OPINIONES ----------------
frases_pos={"producto":["la calidad de la tela es excelente","las zapatillas son muy cómodas","el material se siente premium","me quedó perfecta la talla"],
 "entrega":["llegó antes de lo esperado","el envío fue rápido","llegó en perfecto estado"],
 "atencion":["la atención por WhatsApp fue muy amable","resolvieron mi consulta rápido"],
 "precio":["buen precio con el descuento","vale lo que cuesta"]}
frases_neg={"producto":["la talla vino más pequeña de lo indicado","la costura se descosió a la semana","el color no coincide con la foto","la suela se despegó pronto"],
 "entrega":["el pedido llegó con retraso","el courier no respetó la fecha","la caja llegó dañada"],
 "atencion":["nadie respondió mis mensajes","el proceso de cambio de talla fue lento","la atención al cliente fue deficiente"],
 "precio":["muy caro para la calidad","el envío a provincia cuesta demasiado"]}
pe=pedidos[ent].sample(frac=.38,random_state=1).copy()
late=pe.pedido_id.map(dict(zip(logistica.pedido_id,~logistica.entrega_a_tiempo.fillna(True).astype(bool)))).values
devp=pe.pedido_id.isin(devoluciones.pedido_id).values
score=np.clip(np.round(rng.normal(4.3,0.8,len(pe))-1.4*late-1.6*devp),1,5).astype(int)
txt=[]
for s,l,d in zip(score,late,devp):
    k=rng.integers(1,3); partes=[]
    for _ in range(k):
        asp=rng.choice(["entrega"] if l and rng.random()<.6 else (["producto"] if d and rng.random()<.6 else list(frases_pos)))
        partes.append(rng.choice(frases_neg[asp] if (s<=2 or (s==3 and rng.random()<.5)) else frases_pos[asp]))
    t=", pero ".join(partes) if (s==3 and k==2) else ". ".join(x[0].upper()+x[1:] for x in partes)
    txt.append(t[0].upper()+t[1:]+".")
opiniones=pd.DataFrame({"opinion_id":[f"R{i:06d}" for i in range(1,len(pe)+1)],"pedido_id":pe.pedido_id.values,"cliente_id":pe.cliente_id.values,
  "puntuacion":score,"comentario":txt,"fecha":pe.fecha_pedido.dt.normalize().values+np.timedelta64(1,'D')*rng.integers(3,20,len(pe))})

# ---------------- ATENCIÓN ----------------
nat=int(NP*.09)
pa=pedidos.sample(nat,random_state=2)
atencion=pd.DataFrame({"ticket_id":[f"T{i:05d}" for i in range(1,nat+1)],"cliente_id":pa.cliente_id.values,"pedido_id":pa.pedido_id.values,
 "tipo":rng.choice(["Consulta","Reclamo"],nat,p=[.62,.38]),
 "tema":rng.choice(["Estado del pedido","Cambio de talla","Producto defectuoso","Cobro duplicado","Facturación","Stock"],nat,p=[.32,.25,.14,.07,.1,.12]),
 "canal":rng.choice(["WhatsApp","Email","Web chat","Teléfono"],nat,p=[.5,.2,.2,.1]),
 "fecha":pa.fecha_pedido.dt.normalize().values+np.timedelta64(1,'D')*rng.integers(1,15,nat),
 "horas_resolucion":np.round(rng.lognormal(2.6,0.9,nat),1),
 "resuelto":rng.choice([True,False],nat,p=[.9,.1])})

# ---------------- NAVEGACIÓN (agregado mensual por cliente) ----------------
nav=[]
meses=pd.period_range("2025-01","2026-09",freq="M")
for i in rng.choice(N_CLI,3500,replace=False):
    for m in meses:
        if m.to_timestamp()<clientes.fecha_registro[i]: continue
        if rng.random()<.35: continue
        ses=int(rng.poisson(1+actividad[i]*3))
        if ses==0: continue
        nav.append((clientes.cliente_id[i],str(m),ses,int(ses*rng.uniform(3,9)),round(ses*rng.uniform(2,7),1),
                    rng.choice(["App","Web móvil","Web desktop"],p=[.45,.4,.15]),int(rng.binomial(ses,.3))))
navegacion=pd.DataFrame(nav,columns=["cliente_id","mes","sesiones","paginas_vistas","minutos_totales","dispositivo","carritos_abandonados"])

# ---------------- MARKETING (interacciones) ----------------
mk=[]
for c in campanias.itertuples():
    elig=clientes.cliente_id[clientes.fecha_registro<=c.fecha_inicio].values
    n=min(len(elig),int(len(elig)*.5))
    if n==0: continue
    sel=rng.choice(elig,n,replace=False)
    ab=rng.random(n)<.28; cl=ab&(rng.random(n)<.35)
    mk+= list(zip([c.campania_id]*n,sel,ab,cl))
marketing=pd.DataFrame(mk,columns=["campania_id","cliente_id","abrio","hizo_clic"])

# =============== INYECCIÓN DE PROBLEMAS DE CALIDAD ===============
# Clientes: nulos, edades imposibles, género inconsistente, departamentos mal escritos, duplicados
idx=rng.choice(N_CLI,int(N_CLI*.06),replace=False); clientes.loc[idx,"edad"]=np.nan
idx=rng.choice(N_CLI,14,replace=False); clientes.loc[idx,"edad"]=rng.choice([3,5,150,199,-1,0],14)
idx=rng.choice(N_CLI,int(N_CLI*.04),replace=False); clientes.loc[idx,"genero"]=rng.choice(["masculino","F ","f","Femenino","m"],len(idx))
idx=rng.choice(N_CLI,int(N_CLI*.03),replace=False); clientes.loc[idx,"genero"]=np.nan
idx=rng.choice(N_CLI,int(N_CLI*.05),replace=False); clientes.loc[idx,"departamento"]=clientes.loc[idx,"departamento"].map(
    lambda s:{"Lima":"LIMA","Junín":"Junin","Áncash":"Ancash","Cusco":"Cuzco","Arequipa":"arequipa"}.get(s,s.upper()))
dup=clientes.sample(45,random_state=3); clientes=pd.concat([clientes,dup]).sample(frac=1,random_state=4).reset_index(drop=True)
# Productos: precio nulo y precios atípicos
productos.loc[rng.choice(len(productos),5,replace=False),"precio_lista"]=np.nan
productos.loc[rng.choice(len(productos),3,replace=False),"marca"]=np.nan
# Detalle: cantidades anómalas y negativas, duplicados
idx=rng.choice(len(detalle),40,replace=False); detalle.loc[idx,"cantidad"]=rng.choice([0,-1,50,99],40)
detalle=pd.concat([detalle,detalle.sample(120,random_state=5)]).reset_index(drop=True)
# Pedidos: fechas futuras/formato, montos nulos
idx=rng.choice(NP,25,replace=False); pedidos.loc[idx,"fecha_pedido"]=pd.Timestamp("2030-01-01")
idx=rng.choice(NP,60,replace=False); pedidos.loc[idx,"monto_total"]=np.nan
# Pagos: método vacío, importe que no cuadra
idx=rng.choice(NP,int(NP*.01),replace=False); pagos.loc[idx,"metodo"]=np.nan
idx=rng.choice(NP,80,replace=False); pagos.loc[idx,"importe"]=(pagos.loc[idx,"importe"]*rng.uniform(1.1,2,80)).round(2)
# Logística: distancias negativas, días extremos
idx=rng.choice(NP,30,replace=False); logistica.loc[idx,"distancia_km"]*=-1
idx=rng.choice(np.where(ent)[0],20,replace=False); logistica.loc[idx,"dias_entrega"]=rng.integers(60,120,20)
# Opiniones: puntuación fuera de rango y comentarios vacíos
idx=rng.choice(len(opiniones),15,replace=False); opiniones.loc[idx,"puntuacion"]=rng.choice([0,6,10],15)
idx=rng.choice(len(opiniones),int(len(opiniones)*.05),replace=False); opiniones.loc[idx,"comentario"]=rng.choice(["",None," "],len(idx))
# Atención: tiempos negativos
idx=rng.choice(nat,12,replace=False); atencion.loc[idx,"horas_resolucion"]=-atencion.loc[idx,"horas_resolucion"]

tablas=dict(clientes=clientes,productos=productos,pedidos=pedidos,detalle_pedido=detalle,pagos=pagos,campanias=campanias,
  marketing=marketing,navegacion=navegacion,atencion=atencion,opiniones=opiniones,devoluciones=devoluciones,logistica=logistica)
for k,v in tablas.items():
    v.to_csv(os.path.join(OUT,f"{k}.csv"),index=False)
    print(f"{k:16s} {v.shape}")
