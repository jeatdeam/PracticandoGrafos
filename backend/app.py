from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from servicio import (
    CANTIDAD_USUARIOS,
    MAX_USUARIOS,
    MIN_USUARIOS,
    Project_Streaming,
    peliculas_por_id,
)

app = FastAPI(title="Streaming Grafos API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

project_streaming = Project_Streaming()
project_streaming.iniciar()


def validar_usuario(id_usuario):
    if id_usuario not in project_streaming.usuarios_registrados:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")


@app.post("/api/generar")
def generar(
    cantidad: int = Query(CANTIDAD_USUARIOS, ge=MIN_USUARIOS, le=MAX_USUARIOS),
    semilla: int | None = None,
):
    project_streaming.generar(cantidad, semilla)
    return {"ok": True, "cantidad": cantidad}


@app.get("/api/usuarios")
def listar_usuarios():
    return [project_streaming.usuario_a_json(u) for u in project_streaming.usuarios_registrados]


@app.get("/api/usuarios/{id_usuario}")
def detalle_usuario(id_usuario: int):
    validar_usuario(id_usuario)
    return project_streaming.detalle_usuario(id_usuario)


@app.post("/api/usuarios/{id_usuario}/ver/{movie_id}")
def ver_pelicula(id_usuario: int, movie_id: str):
    validar_usuario(id_usuario)
    if movie_id not in peliculas_por_id:
        raise HTTPException(status_code=404, detail="Película no encontrada")
    return project_streaming.ver_pelicula(id_usuario, movie_id)


@app.get("/api/peliculas")
def catalogo(
    genero: str | None = None,
    q: str | None = None,
    desde: int = Query(0, ge=0),
    limite: int = Query(40, ge=1, le=200),
):
    return project_streaming.catalogo(genero, q, desde, limite)


@app.get("/api/grafo")
def grafo():
    return project_streaming.grafo_json()


@app.get("/api/grafo/{id_usuario}")
def sub_grafo(id_usuario: int):
    validar_usuario(id_usuario)
    return project_streaming.sub_grafo_json(id_usuario)


@app.get("/api/matriz")
def matriz():
    return project_streaming.matriz_adyacencia()
