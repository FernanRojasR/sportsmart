# backend

API que expone los resultados de los modelos (propuesta: FastAPI).

- `api/`: rutas (`/clientes/{id}/segmento`, `/clientes/{id}/riesgo`, `/ventas/pronostico`, `/productos/{id}/recomendaciones`)
- `services/`: lógica que llama a `src/models`
- `models/`: esquemas de entrada/salida (Pydantic)
