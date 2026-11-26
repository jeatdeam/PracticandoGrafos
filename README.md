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
| GET    | `/api/usuarios/{id}`  | Perfil, películas vistas, recomendadas (BFS, director, actor, populares), conexiones |
| GET    | `/api/grafo`          | Grafo completo (usuarios + géneros)                |
| GET    | `/api/grafo/{id}`     | Sub-grafo de un usuario                            |
| GET    | `/api/matriz`         | Matriz de adyacencia                               |
| GET    | `/api/resumen`        | Vértices y aristas del grafo único, por tipo       |
| POST   | `/api/usuarios/{id}/ver/{movie_id}` | El usuario ve una película (se guarda y se recalcula el grafo) |
| GET    | `/api/peliculas?genero=&q=&desde=&limite=` | Catálogo con filtros |
| POST   | `/api/generar?cantidad=25` | Reemplaza todo con N usuarios nuevos (2–300) |

Los usuarios y sus películas vistas se guardan en `backend/streaming.db` (SQLite).
Para empezar desde cero, borra ese archivo y reinicia el backend.

Documentación interactiva de la API: http://127.0.0.1:8000/docs

## Grafo

Un único grafo no dirigido (`backend/grafo.py`, listas de adyacencia):

- Nodos: usuarios (`U:<id>`) y las 1500 películas del CSV (`P:<movie_id>`). Los géneros son atributos.
- Aristas `vista` (usuario–película) y `usuario` (usuario–usuario) cuando comparten género favorito válido
  o tienen películas vistas en común; cada arista guarda `motivos` y `comunes`.
- `/api/grafo` muestra la vista de usuarios de ese mismo grafo (los nodos de género son solo agrupadores visuales).
- `backend/recorridos.py`: BFS (cola FIFO, niveles, padres; candidatos por el camino
  usuario → película → usuario → película y camino mínimo entre usuarios) y DFS iterativo
  (pila; componentes conexas del grafo completo y de la vista de usuarios).
- Recomendaciones por atributo (`recorridos.py`): el director y el actor que más se repiten en las
  aristas `vista` del usuario (empate: orden alfabético) y sus películas no vistas, ordenadas por
  popularidad (grado de la película = cuántos la vieron). La fila "Populares" usa ese mismo grado.

## Pruebas

```bash
cd backend
python -m unittest discover -s tests -v
```

Para comparar los recomendadores (BFS, aleatorio, popularidad, género, director y actor) con Precision@5 y Recall@5:

```bash
cd backend
python evaluar.py
```

Las pruebas de `tests/test_servicio.py` se omiten si faltan las dependencias de `requirements.txt` (y `httpx` para la API).
