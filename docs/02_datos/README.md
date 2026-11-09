# Datos

- `diccionario_datos.xlsx`: diccionario y perfil de las 13 tablas (92 campos), con la hoja `Equivalencia PDF` campo a campo. Se regenera con `python src/data/diccionario.py`.
- `informe_calidad.md`: problemas detectados, impacto y tratamiento propuesto.
- Datos crudos: `data/raw/*.csv` (dataset sintético, semilla 42).

## Tablas

| Tabla | Grano (1 fila = …) | Clave | Se relaciona con |
|---|---|---|---|
| clientes | un cliente | cliente_id | pedidos, navegacion, marketing, atencion, opiniones |
| productos | un producto | producto_id | detalle_pedido, devoluciones, inventario |
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
| inventario | cierre mensual de un producto | producto_id + mes | productos |

## Equivalencia con el dataset de la propuesta (PDF, sección 6)

| Tabla del PDF | Tabla(s) del proyecto | Tipo de equivalencia | Observación |
|---|---|---|---|
| Clientes | `clientes` | Directa | La ubicación se registra como `departamento` |
| Productos | `productos` | Adaptada | La fila del PDF repite los campos de Clientes (edad, ubicación, género, fecha de registro), que no aplican a un producto. Se usan atributos de producto: nombre, categoría, subcategoría, marca, precio y costo |
| Ventas | `pedidos` + `detalle_pedido` | Dividida | Separa la cabecera del pedido de sus ítems, porque un pedido puede tener varios productos |
| Pagos | `pagos` | Directa | |
| Navegación | `navegacion` | Directa | Cada sesión se considera una visita. Es un agregado mensual |
| Marketing | `campanias` + `marketing` | Dividida | Separa la campaña y su canal de la interacción de cada cliente |
| Atención | `atencion` | Directa | Reclamos y consultas se distinguen con `tipo`; el tiempo está en `horas_resolucion` |
| Opiniones | `opiniones` | Directa | |
| Devoluciones | `devoluciones` | Directa | |
| Logística | `logistica` | Directa | |
| Relaciones | Sin tabla propia | Derivada | Se construye en la preparación para grafos (ver abajo) |
| — | `inventario` | Adicional | No la pide el PDF; se agregó para sustentar el problema de quiebres y excesos de stock |

**Relaciones derivables** (sobre ítems y pedidos válidos, `reports/eda.json` → `eda.relaciones`):

| Relación | Cómo se obtiene | Pares distintos |
|---|---|---|
| Cliente-producto | `pedidos` + `detalle_pedido` | 84 477 |
| Cliente-categoría | `pedidos` + `detalle_pedido` + `productos` | 25 147 |
| Producto-producto | Productos que coinciden en un mismo pedido | 15 643 (3 891 coinciden en 5 pedidos o más) |

**Cobertura parcial de `navegacion`:** solo abarca de ene-2025 a sep-2026 y 3 451 clientes (23,0 %). Las variables de navegación no estarán disponibles para todos los clientes al modelar.

## Cómo se simula el inventario

`inventario` se deriva de las ventas y devoluciones simuladas, y cumple `stock_final = stock_inicial + unidades_recibidas + reposicion_urgente − unidades_vendidas + unidades_reingresadas`. Usa una semilla propia para no alterar las otras 12 tablas.

- **Regla de reposición:** cada mes se repone según el promedio de los 3 meses previos, sin considerar estacionalidad. Por eso los picos de demanda producen quiebres.
- **Quiebre:** todas las ventas simuladas ya ocurrieron, así que un faltante se cubre con `reposicion_urgente` y se marca en `quiebre_stock`. `dias_sin_stock` es una estimación proporcional al faltante.
- **Límites:** la tabla no mide ventas perdidas, y los tickets de atención con tema "Stock" se generaron de forma independiente, por lo que no deben usarse como efecto de los quiebres.

## Problemas de calidad intencionales

El generador introduce errores para la fase de comprensión de datos: IDs y filas duplicadas, edades fuera de rango, género y departamento no estandarizados, cantidades ≤ 0 o atípicas, fechas futuras, montos nulos, importes de pago que no cuadran, distancias negativas, días de entrega extremos, puntuaciones fuera de 1–5, comentarios vacíos, horas de resolución negativas, y en inventario recepciones sin registrar o atípicas, stock final negativo y filas duplicadas. El detalle cuantificado está en `reports/eda.json` → `calidad`.

**Nulos estructurales (no son errores):** `talla` en productos sin talla, `campania_id` en compras sin campaña y `dias_entrega` en pedidos cancelados o en tránsito.
