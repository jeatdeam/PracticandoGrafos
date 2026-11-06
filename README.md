# GrafoFlix — Streaming con grafos

Interfaz estilo Netflix (React) + API (FastAPI) sobre la lógica de grafos del proyecto.

```
backend/    API en FastAPI (reutiliza usuario.py y peliculas_streaming_1000.csv)
frontend/   React + Vite, grafo 2D con react-force-graph-2d
main.py     versión original de consola
```

## Cómo ejecutar

Terminal 1 — backend:

```bash
cd backend
pip install -r requirements.txt
python -m uvicorn app:app --reload
```

Terminal 2 — frontend:

```bash
cd frontend
npm install
npm run dev
```

Abrir http://localhost:5173

## Endpoints

| Método | Ruta                  | Descripción                                        |
|--------|-----------------------|----------------------------------------------------|
| GET    | `/api/usuarios`       | Lista de perfiles                                  |
| GET    | `/api/usuarios/{id}`  | Perfil, películas vistas, recomendadas, conexiones |
| GET    | `/api/grafo`          | Grafo completo (usuarios + géneros)                |
| GET    | `/api/grafo/{id}`     | Sub-grafo de un usuario                            |
| GET    | `/api/matriz`         | Matriz de adyacencia                               |
| POST   | `/api/usuarios/{id}/ver/{movie_id}` | El usuario ve una película (se guarda y se recalcula el grafo) |
| GET    | `/api/peliculas?genero=&q=&desde=&limite=` | Catálogo con filtros |
| POST   | `/api/generar?cantidad=25` | Reemplaza todo con N usuarios nuevos (2–300) |

Los usuarios y sus películas vistas se guardan en `backend/streaming.db` (SQLite).
Para empezar desde cero, borra ese archivo y reinicia el backend.

Documentación interactiva de la API: http://127.0.0.1:8000/docs
