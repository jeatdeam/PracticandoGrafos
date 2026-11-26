"""Integración del grafo único con Project_Streaming y la API.

Requiere las dependencias de requirements.txt (pandas, faker, fastapi) y, para
la API, httpx. Si faltan, las pruebas se omiten (skip) en lugar de fallar.
Usa una base SQLite temporal: no toca backend/streaming.db.
"""
import importlib.util
import os
import sys
import tempfile
import unittest

CARPETA_BACKEND = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, CARPETA_BACKEND)

from grafo import MIN_PELICULAS_COMUNES  # noqa: E402

FALTAN = [m for m in ("pandas", "faker") if importlib.util.find_spec(m) is None]
FALTAN_API = [m for m in ("fastapi", "httpx") if importlib.util.find_spec(m) is None]


@unittest.skipIf(FALTAN, f"Faltan dependencias: {', '.join(FALTAN)}")
class TestServicio(unittest.TestCase):

    def setUp(self):
        import servicio
        self.servicio = servicio
        self.temporal = tempfile.TemporaryDirectory()
        self.ruta_original = servicio.RUTA_BD
        servicio.RUTA_BD = os.path.join(self.temporal.name, "prueba.db")
        self.proyecto = servicio.Project_Streaming()
        self.proyecto.generar(cantidad=12, semilla=7)

    def tearDown(self):
        self.servicio.RUTA_BD = self.ruta_original
        self.temporal.cleanup()

    def test_grafo_contiene_usuarios_y_1500_peliculas(self):
        conteo = self.proyecto.resumen()
        self.assertEqual(conteo["vertices"]["usuario"], 12)
        self.assertEqual(conteo["vertices"]["pelicula"], 1500)
        self.assertEqual(conteo["vertices"]["total"], 1512)
        vistas = sum(len(u.get_peliculasVistas()) for u in self.proyecto.usuarios_registrados.values())
        self.assertEqual(conteo["aristas"]["vista"], vistas)

    def test_conexiones_con_motivos_coherentes(self):
        for id_usuario, usuario in self.proyecto.usuarios_registrados.items():
            for conexion in self.proyecto.detalle_usuario(id_usuario)["conexiones"]:
                otro = self.proyecto.usuarios_registrados[conexion["id"]]
                comunes = {p["movie_id"] for p in usuario.get_peliculasVistas()} & {
                    p["movie_id"] for p in otro.get_peliculasVistas()
                }
                self.assertEqual(conexion["peliculas_comunes"], len(comunes))
                self.assertEqual("peliculas" in conexion["motivos"], len(comunes) >= MIN_PELICULAS_COMUNES)
                mismo_genero = usuario.get_generoFav() is not None and usuario.get_generoFav() == otro.get_generoFav()
                self.assertEqual("genero" in conexion["motivos"], mismo_genero)

    def test_formato_compatible_con_frontend(self):
        datos = self.proyecto.grafo_json()
        self.assertEqual(set(datos), {"nodes", "links"})
        tipos = {l["tipo"] for l in datos["links"]}
        self.assertTrue(tipos <= {"genero", "usuario"})
        sub = self.proyecto.sub_grafo_json(0)
        self.assertIn("0", {n["id"] for n in sub["nodes"]})
        matriz = self.proyecto.matriz_adyacencia()
        self.assertEqual(len(matriz["matriz"]), 12)

    def test_vista_separada_por_genero(self):
        """Grafo, sub-grafo y recorridos se dibujan por género: nunca hay aristas
        entre usuarios de géneros distintos y BFS/DFS se quedan en la figura del
        usuario inicial."""
        genero = {u: us.get_generoFav() for u, us in self.proyecto.usuarios_registrados.items()}
        datos = self.proyecto.grafo_json()
        for l in datos["links"]:
            if l["tipo"] == "usuario":
                self.assertIsNotNone(genero[int(l["source"])])
                self.assertEqual(genero[int(l["source"])], genero[int(l["target"])])
        for u in self.proyecto.usuarios_registrados:
            sub = self.proyecto.sub_grafo_json(u)
            usuarios_sub = [int(n["id"]) for n in sub["nodes"] if n["tipo"] == "usuario"]
            generos_sub = [n for n in sub["nodes"] if n["tipo"] == "genero"]
            self.assertEqual(len(generos_sub), 1)  # una sola esfera de género al centro
            if genero[u] is None:
                self.assertEqual(usuarios_sub, [u])
            else:
                self.assertEqual({genero[v] for v in usuarios_sub}, {genero[u]})
                mismos = {v for v, g in genero.items() if g == genero[u]}
                self.assertEqual(set(usuarios_sub), mismos)
            for tipo in ("bfs", "dfs"):
                r = self.proyecto.recorrido(tipo, u)
                self.assertEqual(set(r["miembros"]), set(usuarios_sub))
                self.assertEqual(r["pasos"][0]["nodo"], u)

    def test_ver_pelicula_actualiza_el_grafo(self):
        antes = self.proyecto.resumen()["aristas"]["vista"]
        vistas = {p["movie_id"] for p in self.proyecto.usuarios_registrados[0].get_peliculasVistas()}
        nueva = next(m for m in self.servicio.peliculas_por_id if m not in vistas)
        self.assertTrue(self.proyecto.ver_pelicula(0, nueva)["nueva"])
        self.assertEqual(self.proyecto.resumen()["aristas"]["vista"], antes + 1)

    def test_recomendaciones_por_bfs(self):
        for id_usuario, usuario in self.proyecto.usuarios_registrados.items():
            detalle = self.proyecto.detalle_usuario(id_usuario)
            recomendadas = detalle["recomendadas"]
            self.assertEqual(len(recomendadas), 5)
            vistas = {p["movie_id"] for p in usuario.get_peliculasVistas()}
            self.assertFalse({r["id"] for r in recomendadas} & vistas)
            for r in recomendadas:
                self.assertIn(r["origen"], ("bfs", "popularidad"))
                if r["origen"] == "bfs":
                    self.assertGreaterEqual(r["usuarios_que_la_vieron"], 1)
                    self.assertTrue(r["explicacion"]["usuario"] and r["explicacion"]["pelicula"])
            if vistas:  # con vistas, el BFS da candidatas en esta población
                self.assertEqual(recomendadas[0]["origen"], "bfs")

    def test_filas_por_director_actor_y_popularidad(self):
        for id_usuario, usuario in self.proyecto.usuarios_registrados.items():
            detalle = self.proyecto.detalle_usuario(id_usuario)
            vistas = usuario.get_peliculasVistas()
            ids_vistas = {p["movie_id"] for p in vistas}

            populares = detalle["populares"]
            self.assertEqual(len(populares), self.servicio.PELICULAS_POR_FILA)
            self.assertFalse({p["id"] for p in populares} & ids_vistas)
            self.assertEqual([p["puntaje"] for p in populares], sorted((p["puntaje"] for p in populares), reverse=True))

            for clave, origen in (("por_director", "director"), ("por_actor", "actor")):
                fila = detalle[clave]
                if not vistas:
                    self.assertIsNone(fila["nombre"])
                    self.assertEqual(fila["peliculas"], [])
                    continue
                self.assertGreaterEqual(fila["vistas"], 1)
                self.assertEqual(len(fila["peliculas"]), self.servicio.PELICULAS_POR_FILA)
                for p in fila["peliculas"]:
                    self.assertNotIn(p["id"], ids_vistas)
                    self.assertEqual(p["origen"], origen)
                    if origen == "director":
                        self.assertEqual(p["director"], fila["nombre"])
                    else:
                        self.assertIn(fila["nombre"], p["actores"])

            if vistas:  # el favorito es el que más se repite en lo que vio
                directores = [p["director"] for p in vistas]
                self.assertEqual(directores.count(detalle["por_director"]["nombre"]), max(directores.count(d) for d in directores))

    def test_kruskal_en_la_app(self):
        k = self.proyecto.kruskal()
        self.assertEqual(k["arboles"], k["componentes_dfs"])
        self.assertEqual(len(k["aristas"]), 12 - k["arboles"])
        self.assertEqual(k["aristas_grafo"], self.proyecto.resumen()["aristas"]["usuario"])
        self.assertTrue(all(0 <= a["peso"] <= 1 for a in k["aristas"]))

    def test_recomendaciones_se_recalculan_al_ver(self):
        antes = self.proyecto.detalle_usuario(0)["recomendadas"]
        pelicula = antes[0]["id"]
        self.proyecto.ver_pelicula(0, pelicula)
        despues = self.proyecto.detalle_usuario(0)["recomendadas"]
        self.assertNotIn(pelicula, {r["id"] for r in despues})


@unittest.skipIf(FALTAN + FALTAN_API, f"Faltan dependencias: {', '.join(FALTAN + FALTAN_API)}")
class TestApi(unittest.TestCase):

    def test_endpoints_existentes_y_resumen(self):
        import servicio
        temporal = tempfile.TemporaryDirectory()
        original = servicio.RUTA_BD
        servicio.RUTA_BD = os.path.join(temporal.name, "api.db")
        try:
            from fastapi.testclient import TestClient
            import app
            cliente = TestClient(app.app)
            self.assertEqual(cliente.post("/api/generar?cantidad=5&semilla=3").status_code, 200)
            for ruta in ("/api/usuarios", "/api/usuarios/0", "/api/grafo", "/api/grafo/0", "/api/matriz", "/api/resumen"):
                self.assertEqual(cliente.get(ruta).status_code, 200, ruta)
            self.assertEqual(cliente.get("/api/resumen").json()["vertices"]["pelicula"], 1500)
            self.assertEqual(cliente.get("/api/recorrido/xyz/0").status_code, 400)
            kruskal = cliente.get("/api/kruskal")
            self.assertEqual(kruskal.status_code, 200)
            self.assertEqual(kruskal.json()["arboles"], kruskal.json()["componentes_dfs"])
            for tipo in ("bfs", "dfs"):
                respuesta = cliente.get(f"/api/recorrido/{tipo}/0?todo=true")
                self.assertEqual(respuesta.status_code, 200)
                datos = respuesta.json()
                self.assertEqual(datos["tipo"], tipo)
                self.assertEqual(datos["miembros"], [0, 1, 2, 3, 4])  # todo=true recorre a los 5 usuarios
                self.assertEqual(len(datos["pasos"]), 5)
        finally:
            servicio.RUTA_BD = original
            temporal.cleanup()


if __name__ == "__main__":
    unittest.main()
