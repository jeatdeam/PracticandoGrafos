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
