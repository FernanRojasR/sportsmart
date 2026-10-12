# Arquitectura de la plataforma

```
 data/raw ──► src/data ──► src/features ──► data/processed
                                   │
                                   ▼
                              src/models ──► src/evaluation / src/explainability
                                   │
                                   ▼
                      backend/api (FastAPI) ◄── src/monitoring
                                   │
                                   ▼
                          frontend (dashboard)
```

| Capa | Responsabilidad |
|---|---|
| `src/data` | Generar / cargar / validar datos crudos |
| `src/features` | Limpieza, integración y variables (RFM, recencia, frecuencia, etc.) |
| `src/models` | Entrenamiento y persistencia de modelos |
| `src/evaluation` | Métricas y comparación de modelos |
| `src/explainability` | SHAP, importancia de variables, interpretación de segmentos |
| `src/monitoring` | Deriva de datos y desempeño en el tiempo |
| `backend` | API que sirve predicciones y segmentos |
| `frontend` | Dashboard para usuarios de negocio |

Agregar aquí diagramas (componentes, despliegue, casos de uso) a medida que se definan.
