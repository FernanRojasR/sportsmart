# KPIs de negocio — SportSmart Perú

Los KPIs miden el resultado para el negocio. Las métricas de calidad de cada modelo (AUC, MAPE, silhouette, etc.) están aparte, en los criterios de éxito de [`crisp_dm.md`](../01_metodologia/crisp_dm.md).

## Cómo leer las tablas

- **Línea base:** últimos 12 meses cerrados (oct-2025 a sep-2026), salvo que la fórmula indique otra ventana. Se calcula con registros válidos en `src/data/eda_calidad.py` y queda en `reports/eda.json`, sección `kpis`.
- **Meta:** valor propuesto a 12 meses de implementar la plataforma. Debe validarse con el docente.
- **Pedidos válidos:** no cancelados, con monto y con fecha dentro del periodo.

## KPIs principales para la presentación

| KPI | Línea base | Meta |
|---|---|---|
| C1 · Activación a 90 días | 44,5 % | ≥ 50 % |
| C2 · Retención anual | 46,1 % | ≥ 51 % |
| V1 · Crecimiento interanual de ventas | 10,0 % | ≥ 12 % |
| M2 · Conversión de campañas | 3,2 % | ≥ 5 % |
| L1 · Entregas a tiempo | 89,5 % | ≥ 92 % |
| I2 · Quiebre de stock en noviembre-diciembre | 28,5 % | ≤ 15 % |

## Catálogo completo

### Ventas (Gerencia comercial)

| ID | KPI | Fórmula | Línea base | Meta | Palanca (objetivo específico) |
|---|---|---|---|---|---|
| V1 | Crecimiento interanual de ventas | (Ventas de los últimos 12 meses ÷ ventas de los 12 meses anteriores − 1) × 100 | 10,0 % (S/ 4 353 865 en 12 meses) | ≥ 12 % | Segmentación y campañas dirigidas (3), pronóstico (4) |
| V2 | Ticket promedio | Ventas ÷ número de pedidos válidos | S/ 229,42 | ≥ S/ 240 | Reglas de asociación para paquetes y recomendaciones (2) |

### Clientes (Marketing)

| ID | KPI | Fórmula | Línea base | Meta | Palanca (objetivo específico) |
|---|---|---|---|---|---|
| C1 | Activación a 90 días | Clientes registrados entre jul-2025 y jun-2026 con primera compra válida en 90 días ÷ clientes registrados en ese periodo × 100 | 44,5 % | ≥ 50 % | Segmentación (3) |
| C2 | Retención anual | Compradores de oct-2024 a sep-2025 que volvieron a comprar entre oct-2025 y sep-2026 ÷ compradores de oct-2024 a sep-2025 × 100 | 46,1 % | ≥ 51 % | Predicción de abandono (7), explicabilidad (9) |
| C3 | Inactividad a 180 días | Compradores con última compra hace más de 180 días al cierre ÷ total de compradores históricos × 100 | 70,9 % | ≤ 65 % | Predicción de abandono (7) |

> C3 usa toda la historia desde 2023, así que incluye clientes que se fueron hace años y baja lentamente. Para evaluar la gestión del año, C2 es más sensible.

### Marketing (Marketing)

| ID | KPI | Fórmula | Línea base | Meta | Palanca (objetivo específico) |
|---|---|---|---|---|---|
| M1 | CTR de campañas | Clientes con clic ÷ clientes impactados × 100, en campañas iniciadas en el periodo | 9,6 % | ≥ 12 % | Segmentación (3) |
| M2 | Conversión de campañas | Clientes impactados que compraron con esa campaña ÷ clientes impactados × 100 | 3,2 % | ≥ 5 % | Segmentación (3), asociación (2) |
| M3 | Carritos abandonados | Carritos abandonados ÷ sesiones × 100 | 30,2 % | ≤ 27 % | Recomendaciones (2), grafos (5) |

### Logística e inventario (Logística)

| ID | KPI | Fórmula | Línea base | Meta | Palanca (objetivo específico) |
|---|---|---|---|---|---|
| L1 | Entregas a tiempo | Envíos con `dias_entrega` ≤ `dias_prometidos` ÷ envíos entregados × 100 | 89,5 % | ≥ 92 % | Análisis de opiniones (8), pronóstico (4) |
| I1 | Quiebre de stock | Productos-mes con quiebre ÷ total de productos-mes × 100 | 11,0 % | ≤ 8 % | Pronóstico (4) |
| I2 | Quiebre de stock en temporada alta | Igual que I1, solo noviembre y diciembre de 2025 | 28,5 % | ≤ 15 % | Pronóstico (4) |
| I3 | Exceso de stock | Productos-mes con stock final mayor a 2 meses de venta media del producto ÷ total de productos-mes × 100 | 11,9 % | ≤ 9 % | Pronóstico (4) |

### Postventa (Atención al cliente)

| ID | KPI | Fórmula | Línea base | Meta | Palanca (objetivo específico) |
|---|---|---|---|---|---|
| P1 | Tasa de devolución | Ítems devueltos ÷ ítems entregados × 100 | 6,8 % | ≤ 6 % | Análisis de opiniones (8): talla incorrecta es el principal motivo, con 35,0 % de las devoluciones |
| P2 | Reclamos por cada 100 pedidos | Tickets de tipo Reclamo ÷ pedidos válidos × 100 | 3,71 | ≤ 3,2 | Análisis de opiniones (8) |
| P3 | Tiempo de resolución | Mediana de `horas_resolucion` de los tickets | 13,4 h | ≤ 12 h | Análisis de temas de reclamos (8) |
| P4 | Puntuación media | Promedio de `puntuacion` de reseñas válidas | 3,93 | ≥ 4,1 | Análisis de opiniones (8) |

## Criterios usados para proponer las metas

- **Referencias internas cuando existen:** I1 toma como referencia el 7,7 % de quiebres fuera de temporada alta, y P4 la puntuación de 4,08 con entrega a tiempo.
- **Mejoras graduales en los demás casos:** cambios alcanzables en 12 meses, como +5 puntos en retención.

## Límites

- **Datos simulados:** el proyecto no opera sobre clientes reales, así que las metas son objetivos propuestos y no podrán comprobarse después del despliegue.
- **M1 y M2:** en la simulación, los envíos de campaña y las compras se generan por separado, así que la línea base no refleja un efecto real de las campañas.
- **I1, I2 e I3:** dependen de la regla de reposición simulada, descrita en [`docs/02_datos/README.md`](../02_datos/README.md).
