import os
import re
import random
import sqlite3
import sys
from contextlib import contextmanager

import pandas as pd
from faker import Faker

# Reutilizamos la clase Usuario del proyecto original (carpeta raíz)
RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(RAIZ)
from usuario import Usuario  # noqa: E402

CANTIDAD_USUARIOS = 25
MIN_USUARIOS, MAX_USUARIOS = 2, 300
CANTIDAD_PELICULAS_VISTAS = 100
PELICULAS_A_RECOMENDAR = 5
SIN_GENERO = "sin peliculas vistas"

RUTA_BD = os.path.join(os.path.dirname(os.path.abspath(__file__)), "streaming.db")

datos = pd.read_csv(os.path.join(RAIZ, "peliculas_streaming_1000.csv"))
peliculas_por_id = {p["movie_id"]: p for p in datos.to_dict(orient="records")}
fake = Faker("es_ES")


def limpiar_titulo(titulo):
    return re.sub(r"\d", "", titulo).strip()


def pelicula_a_json(pelicula):
    return {
        "id": pelicula["movie_id"],
        "titulo": limpiar_titulo(pelicula["titulo"]),
        "director": pelicula["director"],
        "genero": pelicula["genero"],
        "presupuesto": int(pelicula["presupuesto_usd_m"]),
        "actores": pelicula["actores"],
        "tipo": pelicula["tipo"],
    }


# ------------------------------- Base de datos -------------------------------

@contextmanager
def conectar():
    """Abre la base, confirma los cambios al terminar y la cierra."""
    con = sqlite3.connect(RUTA_BD)
    con.execute("PRAGMA foreign_keys = ON")
    try:
        with con:
            yield con
    finally:
        con.close()


def crear_tablas():
    with conectar() as con:
        con.executescript(
            """
            CREATE TABLE IF NOT EXISTS usuarios (
                id       INTEGER PRIMARY KEY,
                nombre   TEXT NOT NULL,
                apellido TEXT NOT NULL,
                correo   TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS vistas (
                orden      INTEGER PRIMARY KEY AUTOINCREMENT,
                usuario_id INTEGER NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
                movie_id   TEXT NOT NULL,
                UNIQUE (usuario_id, movie_id)
            );
            """
        )


class Project_Streaming:

    def __init__(self):
        self.usuarios_registrados = {}
        self.grafo = {}
        self.recomendaciones = {}
        crear_tablas()

    def iniciar(self):
        """Carga los usuarios guardados. Si la base está vacía, el frontend
        pregunta cuántos generar."""
        self.cargar()

    def generar(self, cantidad=CANTIDAD_USUARIOS, semilla=None):
        if semilla is not None:
            random.seed(semilla)
            Faker.seed(semilla)
        self.generar_usuarios(cantidad)
        self.asignar_peliculas()
        self.guardar()
        self.actualizar()

    def actualizar(self):
        """Recalcula géneros favoritos, grafo y recomendaciones."""
        for usuario in self.usuarios_registrados.values():
            usuario.obtener_generos_vistos()
        self.generar_grafo()
        self.generar_recomendaciones()

    def generar_usuarios(self, cantidad):
        self.usuarios_registrados = {}
        for indice in range(cantidad):
            self.usuarios_registrados[indice] = Usuario(
                fake.first_name(), fake.last_name(), fake.email(), indice
            )

    def asignar_peliculas(self):
        for usuario in self.usuarios_registrados.values():
            for _ in range(random.randint(0, CANTIDAD_PELICULAS_VISTAS)):
                posicion_random = random.randint(0, len(datos) - 1)
                usuario.ver_pelicula(datos.iloc[posicion_random].to_dict())

    def guardar(self):
        with conectar() as con:
            con.execute("DELETE FROM vistas")
            con.execute("DELETE FROM usuarios")
            con.execute("DELETE FROM sqlite_sequence WHERE name = 'vistas'")
            for id_usuario, u in self.usuarios_registrados.items():
                con.execute(
                    "INSERT INTO usuarios (id, nombre, apellido, correo) VALUES (?, ?, ?, ?)",
                    (id_usuario, u.nombre, u.apellido, u.correo),
                )
                con.executemany(
                    "INSERT INTO vistas (usuario_id, movie_id) VALUES (?, ?)",
                    [(id_usuario, p["movie_id"]) for p in u.get_peliculasVistas()],
                )

    def cargar(self):
        with conectar() as con:
            filas = con.execute("SELECT id, nombre, apellido, correo FROM usuarios ORDER BY id").fetchall()
            vistas = con.execute("SELECT usuario_id, movie_id FROM vistas ORDER BY orden").fetchall()

        if not filas:
            return False

        self.usuarios_registrados = {
            id_usuario: Usuario(nombre, apellido, correo, id_usuario)
            for id_usuario, nombre, apellido, correo in filas
        }
        for id_usuario, movie_id in vistas:
            if movie_id in peliculas_por_id:
                self.usuarios_registrados[id_usuario].ver_pelicula(peliculas_por_id[movie_id])

        self.actualizar()
        return True

    def ver_pelicula(self, id_usuario, movie_id):
        """Registra que el usuario vio la película, la guarda en la base y actualiza el grafo."""
        usuario = self.usuarios_registrados[id_usuario]
        genero_anterior = usuario.get_generoFav()
        cantidad_antes = len(usuario.get_peliculasVistas())

        usuario.ver_pelicula(peliculas_por_id[movie_id])
        nueva = len(usuario.get_peliculasVistas()) > cantidad_antes

        if nueva:
            with conectar() as con:
                con.execute(
                    "INSERT OR IGNORE INTO vistas (usuario_id, movie_id) VALUES (?, ?)",
                    (id_usuario, movie_id),
                )
            self.actualizar()

        return {
            "nueva": nueva,
            "genero_anterior": genero_anterior,
            "usuario": self.detalle_usuario(id_usuario),
        }

    def generar_grafo(self):
        # Conectamos usuarios que comparten el mismo género favorito
        self.grafo = {}
        for id_1, usuario_1 in self.usuarios_registrados.items():
            self.grafo[id_1] = [
                id_2
                for id_2, usuario_2 in self.usuarios_registrados.items()
                if id_1 != id_2 and usuario_1.get_generoFav() == usuario_2.get_generoFav()
            ]

    def generar_recomendaciones(self):
        self.recomendaciones = {}
        for id_usuario, usuario in self.usuarios_registrados.items():
            vistas = {p["titulo"] for p in usuario.get_peliculasVistas()}
            filtradas = datos[datos["genero"] == str(usuario.genero_preferido)]
            recomendadas = [
                p for p in filtradas.to_dict(orient="records") if p["titulo"] not in vistas
            ]
            self.recomendaciones[id_usuario] = recomendadas[:PELICULAS_A_RECOMENDAR]

    # ------------------------- Serialización para la API -------------------------

    def catalogo(self, genero=None, busqueda=None, desde=0, limite=40):
        filtradas = datos
        if genero:
            filtradas = filtradas[filtradas["genero"] == genero]
        if busqueda:
            texto = busqueda.lower()
            filtradas = filtradas[
                filtradas["titulo"].str.lower().str.contains(texto, regex=False)
                | filtradas["director"].str.lower().str.contains(texto, regex=False)
                | filtradas["actores"].str.lower().str.contains(texto, regex=False)
            ]
        pagina = filtradas.iloc[desde: desde + limite].to_dict(orient="records")
        return {
            "total": len(filtradas),
            "generos": sorted(datos["genero"].unique().tolist()),
            "peliculas": [pelicula_a_json(p) for p in pagina],
        }

    def usuario_a_json(self, id_usuario):
        usuario = self.usuarios_registrados[id_usuario]
        return {
            "id": id_usuario,
            "nombre": usuario.nombre,
            "apellido": usuario.apellido,
            "correo": usuario.correo,
            "genero_favorito": usuario.get_generoFav(),
            "cantidad_vistas": len(usuario.get_peliculasVistas()),
        }

    def detalle_usuario(self, id_usuario):
        usuario = self.usuarios_registrados[id_usuario]
        conteo = {}
        for p in usuario.get_peliculasVistas():
            conteo[p["genero"]] = conteo.get(p["genero"], 0) + 1
        return {
            **self.usuario_a_json(id_usuario),
            # Las más recientes primero
            "peliculas_vistas": [pelicula_a_json(p) for p in reversed(usuario.get_peliculasVistas())],
            "recomendadas": [pelicula_a_json(p) for p in self.recomendaciones[id_usuario]],
            "generos": dict(sorted(conteo.items(), key=lambda x: -x[1])),
            "conexiones": [self.usuario_a_json(v) for v in self.grafo[id_usuario]],
        }

    def grafo_json(self, nodos_usuario=None):
        """Grafo usuarios + géneros (igual que grafico_grafo). Si se pasa una lista
        de nodos, devuelve solo ese sub-grafo (igual que mostrar_subGrafo)."""
        ids = list(self.usuarios_registrados) if nodos_usuario is None else nodos_usuario
        nodos, aristas, agregadas, generos = [], [], set(), set()

        for u in ids:
            usuario = self.usuarios_registrados[u]
            genero = usuario.genero_preferido or SIN_GENERO
            generos.add(genero)
            nodos.append({"id": str(u), "label": f"{usuario.nombre}-{u}", "tipo": "usuario", "genero": genero})
            aristas.append({"source": f"g:{genero}", "target": str(u), "tipo": "genero"})

            for v in self.grafo[u]:
                if v in ids and (u, v) not in agregadas:
                    aristas.append({"source": str(u), "target": str(v), "tipo": "usuario"})
                    agregadas.add((u, v))
                    agregadas.add((v, u))

        for genero in generos:
            nodos.append({"id": f"g:{genero}", "label": genero, "tipo": "genero", "genero": genero})

        return {"nodes": nodos, "links": aristas}

    def sub_grafo_json(self, id_usuario):
        return self.grafo_json([id_usuario] + self.grafo[id_usuario])

    def matriz_adyacencia(self):
        nodos = sorted(self.grafo)
        return {
            "nodos": [self.usuarios_registrados[n].nombre for n in nodos],
            "matriz": [[1 if j in self.grafo[i] else 0 for j in nodos] for i in nodos],
        }
