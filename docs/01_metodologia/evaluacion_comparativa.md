# Evaluación comparativa — SportSmart Perú

Fase CRISP-DM: **Evaluación**. Cubre las técnicas de las semanas 10 y 13. Este documento se genera con `python -m src.evaluation.comparacion` a partir de los reportes de cada técnica.

## 1. Resumen

**5 de 5 técnicas** cumplen su meta y **5 de 5** superan a su referencia simple. 3 análisis complementarios no alcanzan el nivel esperado y se reportan en la sección 4.

> Los datos son simulados: estos resultados evalúan el método y reflejan patrones incorporados al generar el dataset. No demuestran un impacto real en el negocio.

## 2. Resultados frente a metas y referencias

| Técnica | Modelo elegido | Métrica | Resultado | Meta | ¿Cumple? | Referencia simple | Valor de referencia | Validación |
|---|---|---|---|---|---|---|---|---|
| Asociación | FP-Growth, por subcategoría | Reglas con lift > 1,5 y soporte ≥ 1 % | 58 | Al menos 1 regla | Sí | Canastas al azar | 0,0 | 61 de 61 reglas mantienen el lift en el año siguiente |
| Clustering | K-Means sobre RFM, 3 segmentos | Silhouette | 0,412 | > 0,4 | Sí | Tercios de puntaje RFM | 0,214 | ARI de 0,986 con submuestras de 80 % |
| Series temporales | Prophet con calendario y campañas | MAPE semanal (%) | 5,78 | < 15 % | Sí | Mismo día hace 52 semanas | 9,14 | Últimos 6 meses, 4 orígenes y temporada alta 2025 |
| Grafos | Louvain sobre producto-producto | Modularidad | 0,356 | > 0,3 | Sí | Compras al azar | 0,169 | ARI de 0,963 entre semillas |
| Regresión | XGBoost, por producto y mes | R² | 0,735 | > 0,6 | Sí | Promedio móvil 3 meses | 0,643 | Abril a setiembre de 2026, con hiperparámetros validados en el pasado |

## 3. ¿La mejora sobre la referencia es real?

Intervalos de confianza de 95 % obtenidos por remuestreo (bootstrap). Si el intervalo de mejora no incluye el cero, la diferencia no se explica por azar en el periodo evaluado.

| Técnica | Modelo | Referencia | Mejora |
|---|---|---|---|
| Series temporales (MAPE semanal, %) | 4,21 a 7,39 | 6,66 a 11,86 | 0,07 a 6,71 puntos |
| Regresión (R²) | 0,704 a 0,763 | 0,579 a 0,701 | 0,049 a 0,135 |

En series temporales, el límite inferior de la mejora es de solo 0,07 puntos: Prophet probablemente es mejor que la referencia, pero con 25 semanas esa ventaja es incierta. En regresión, con 321 productos, la mejora es más clara.

En asociación, las canastas al azar generan en promedio 0,0 reglas; en grafos, la modularidad con compras al azar no supera 0,178.

## 4. Resultados que no alcanzan lo esperado

| Análisis | Resultado | Esperado | Causa | Decisión |
|---|---|---|---|---|
| MAPE diario de ventas | 16,61 % | < 15 % | Las ventas de cada día son muy variables | Usar el pronóstico para planificar por semana o periodo |
| Gasto futuro del cliente | R² medio de 0,490 | R² > 0,6 | 73,4 % de los compradores no gasta en los 12 meses siguientes | Análisis secundario; evaluar un modelo de dos etapas con el de abandono |
| Agrupación de productos | Silhouette de 0,241 | Sin meta propia; 0,4 en clientes | Los productos no forman grupos bien separados | Usar ABC/XYZ para decisiones de producto |

## 5. Comparación dentro de cada técnica

### Asociación (soporte mínimo 1 %)

| Algoritmo | Conjuntos | Memoria máxima (MB) | Resultados idénticos |
|---|---|---|---|
| Apriori | 60 | 34,86 | Sí |
| FP-Growth | 60 | 0,18 | Sí |
| ECLAT | 60 | 0,28 | Sí |

### Clustering

| Algoritmo | Silhouette | Davies-Bouldin | Grupos | Ruido (%) |
|---|---|---|---|---|
| K-Means RFM (k=3) | 0,412 | 0,917 | 3 | 0,0 |
| K-Means LRFM (k=3) | 0,383 | 1,019 | 3 | 0,0 |
| Jerárquico Ward RFM (k=3) | 0,383 | 0,958 | 3 | 0,0 |
| DBSCAN RFM (eps=0,35) | 0,240 | 0,801 | 3 | 3,6 |

### Series temporales

| Modelo | MAPE semanal (%) | MAPE diario (%) | MAPE semanal en temporada alta (%) |
|---|---|---|---|
| Prophet | 5,78 | 16,61 | 5,68 |
| Referencia (mismo día hace 52 semanas) | 9,14 | 23,26 | 8,81 |
| SARIMA | 11,56 | 18,92 | 30,27 |
| SARIMAX | 11,60 | 17,03 | 5,63 |

### Grafos

| Red | Modularidad |
|---|---|
| Producto-producto, 5 o más pedidos en común | 0,356 |
| Producto-producto, todas las conexiones | 0,302 |
| Compras al azar (promedio) | 0,169 |

### Regresión

| Modelo | R² de validación | R² de prueba | RMSE (S/) | WAPE (%) |
|---|---|---|---|---|
| Referencia (promedio móvil 3 meses) | — | 0,643 | 594,4 | 36,7 |
| Regresión lineal simple | — | 0,651 | 588,0 | 36,6 |
| Regresión múltiple | 0,715 | 0,751 | 497,0 | 32,0 |
| Ridge | 0,715 | 0,751 | 497,0 | 32,0 |
| Lasso | 0,715 | 0,751 | 496,4 | 31,9 |
| Elastic Net | 0,711 | 0,750 | 497,4 | 32,0 |
| Random Forest | 0,716 | 0,743 | 504,9 | 31,6 |
| Gradient Boosting | 0,716 | 0,740 | 507,6 | 31,6 |
| XGBoost (elegido) | 0,723 | 0,735 | 511,8 | 31,6 |

El modelo se eligió por su resultado de validación. Ridge, Lasso y la regresión múltiple obtienen un R² de prueba algo mayor, con diferencias pequeñas.

## 6. Respuestas a las preguntas de negocio

La numeración corresponde a `docs/00_proyecto/idea_proyecto.md`. Las preguntas 12, 13, 16, 17 y 18 se abordan en la semana 16.

| N.° | Pregunta | Respuesta |
|---|---|---|
| 1 | ¿Qué segmentos de clientes existen? | Tres: Alto valor activos, Valiosos inactivos y Ocasionales inactivos. |
| 2 | ¿Qué clientes presentan mayor valor? | Alto valor activos: 14,9 % de los compradores y mediana de CLV de S/ 540. Valiosos inactivos aportó 57,0 % de las ventas históricas. |
| 3 | ¿Qué clientes presentan características similares? | Los de cada segmento y comunidad; 88,0 % comparte deporte con su cliente más parecido. |
| 4 | ¿Cómo evolucionan las ventas? | Crecen y son estacionales; los días de quincena venden 26 % más. |
| 5 | ¿Cuál es la tendencia futura de las ventas? | Se esperan S/ 1 358 062 en 90 días, 10,7 % sobre el mismo periodo anterior. |
| 6 | ¿Qué factores explican las ventas? | Domina el historial de ventas; luego precio y costo, y campañas. Las visitas no agregan capacidad predictiva. |
| 7 | ¿Qué productos se compran conjuntamente? | Por subcategoría, por ejemplo Casaca cortaviento y Jogger. |
| 8 | ¿Qué productos tienen mayor asociación? | 58 reglas superan la meta; el lift máximo es 12,70. |
| 9 | ¿Qué productos presentan comportamientos similares? | Dos grupos débiles de alta y baja rotación; ABC/XYZ resulta más útil. |
| 10 | ¿Cuál será el volumen de ventas esperado? | Por producto y mes, con R² de 0,735; el error total mensual es de 5,8 %. |
| 11 | ¿Cuánto gastará un cliente? | Solo aproximado: R² medio de 0,490, bajo la meta. |
| 14 | ¿Qué productos, clientes o categorías están fuertemente conectados? | Destacan los Tomatodos como conectores. Entre categorías, solo Calzado y Accesorios. |
| 15 | ¿Qué comunidades o patrones pueden encontrarse? | Tres comunidades: Running y fútbol (48,6 % de ingresos), Training y yoga (32,5 %) y Outdoor (13,1 %). |

## 7. Relación con los KPIs de negocio

Los modelos ofrecen herramientas para mejorar estos indicadores. Con datos simulados no se puede medir su efecto real.

| Técnica | KPIs relacionados | Uso propuesto |
|---|---|---|
| Asociación | V2 Ticket promedio; M2 Conversión de campañas; M3 Carritos abandonados | Paquetes y recomendaciones |
| Clustering | C1 Activación; M1 CTR; M2 Conversión | Campañas distintas por segmento |
| Series temporales | V1 Crecimiento; I1, I2 e I3 Quiebres y excesos | Compras anticipadas para la temporada alta |
| Grafos | M3 Carritos abandonados; V2 Ticket promedio | Recomendaciones por comunidad deportiva |
| Regresión | I1 e I3 Quiebres y excesos | Estimar la demanda de cada producto |
