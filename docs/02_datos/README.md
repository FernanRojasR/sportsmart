# Datos

- `diccionario_datos.xlsx`: diccionario y perfil de las 12 tablas (82 campos). Se regenera con `python src/data/diccionario.py`.
- Datos crudos: `data/raw/*.csv` (dataset sintético, semilla 42).

## Tablas

| Tabla | Grano (1 fila = …) | Clave | Se relaciona con |
|---|---|---|---|
| clientes | un cliente | cliente_id | pedidos, navegacion, marketing, atencion, opiniones |
| productos | un producto | producto_id | detalle_pedido, devoluciones |
| pedidos | un pedido | pedido_id | clientes, campanias, detalle_pedido, pagos, logistica |
| detalle_pedido | un ítem de un pedido | pedido_id + producto_id | pedidos, productos |
| pagos | un pago | pago_id | pedidos |
| campanias | una campaña | campania_id | pedidos, marketing |
| marketing | un envío de campaña a un cliente | campania_id + cliente_id | campanias, clientes |
| navegacion | actividad mensual de un cliente | cliente_id + mes | clientes |
| atencion | un ticket | ticket_id | clientes, pedidos |
| opiniones | una reseña | opinion_id | pedidos, clientes |
| devoluciones | una devolución | devolucion_id | pedidos, productos |
| logistica | un envío | envio_id | pedidos |

## Problemas de calidad intencionales

El generador introduce errores para la fase de comprensión de datos: IDs y filas duplicadas, edades fuera de rango, género y departamento no estandarizados, cantidades ≤ 0 o atípicas, fechas futuras, montos nulos, importes de pago que no cuadran, distancias negativas, días de entrega extremos, puntuaciones fuera de 1–5, comentarios vacíos y horas de resolución negativas. El detalle cuantificado está en `reports/eda.json` → `calidad`.

**Nulos estructurales (no son errores):** `talla` en productos sin talla, `campania_id` en compras sin campaña y `dias_entrega` en pedidos cancelados o en tránsito.
