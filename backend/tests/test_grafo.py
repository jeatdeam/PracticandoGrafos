"""Pruebas del grafo único (solo biblioteca estándar).

Ejecutar desde backend/:  python -m unittest discover -s tests -v
"""
import csv
import os
import sys
import unittest

CARPETA_BACKEND = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, CARPETA_BACKEND)

from grafo import (  # noqa: E402
    ARISTA_USUARIO,
    ARISTA_VISTA,
    MOTIVO_GENERO,
    MIN_PELICULAS_COMUNES,
    MOTIVO_PELICULAS,
    construir_grafo,
    motivos_conexion,
    nodo_pelicula,
    nodo_usuario,
)
from usuario import Usuario  # noqa: E402

# Catálogo mínimo: 4 películas, 2 géneros

def construir_k1(peliculas, usuarios):
    """Grafos de prueba pequeños: basta 1 película en común para conectar."""
    return construir_grafo(peliculas, usuarios, min_comunes=1)

PELICULAS = [
    {"movie_id": "M1", "titulo": "Uno", "genero": "Drama"},
    {"movie_id": "M2", "titulo": "Dos", "genero": "Drama"},
    {"movie_id": "M3", "titulo": "Tres", "genero": "Terror"},
    {"movie_id": "M4", "titulo": "Cuatro", "genero": "Terror"},
]


def usuario(genero, vistas, nombre="x"):
    return {"nombre": nombre, "genero_favorito": genero, "vistas": vistas}


class TestNodos(unittest.TestCase):

    def test_peliculas_y_usuarios_son_nodos_reales(self):
        g = construir_k1(PELICULAS, {0: usuario("Drama", ["M1"]), 1: usuario(None, [])})
        for p in PELICULAS:
            self.assertEqual(g.nodos[nodo_pelicula(p["movie_id"])]["tipo"], "pelicula")
        self.assertEqual(g.nodos[nodo_usuario(0)]["tipo"], "usuario")
        self.assertEqual(g.nodos[nodo_usuario(1)]["tipo"], "usuario")
        self.assertEqual(set(g.adyacencia), set(g.nodos))

    def test_identificadores_sin_colision(self):
        # Una película cuyo id coincide con el de un usuario sigue siendo otro nodo
        g = construir_k1([{"movie_id": "7", "genero": "Drama"}], {7: usuario("Drama", ["7"])})
        self.assertNotEqual(nodo_usuario(7), nodo_pelicula("7"))
        self.assertEqual(g.conteo()["vertices"]["total"], 2)
        self.assertEqual(g.arista(nodo_usuario(7), nodo_pelicula("7"))["tipo"], ARISTA_VISTA)

    def test_generos_no_son_nodos(self):
        g = construir_k1(PELICULAS, {0: usuario("Drama", ["M1"])})
        self.assertEqual({a["tipo"] for a in g.nodos.values()}, {"usuario", "pelicula"})


class TestAristasVista(unittest.TestCase):

    def test_una_arista_por_pelicula_vista(self):
        g = construir_k1(PELICULAS, {0: usuario("Drama", ["M1", "M2"])})
        self.assertEqual(sorted(g.vecinos(nodo_usuario(0), ARISTA_VISTA)), [nodo_pelicula("M1"), nodo_pelicula("M2")])
        self.assertIn(nodo_usuario(0), g.vecinos(nodo_pelicula("M1")))  # no dirigido

    def test_ignora_peliculas_fuera_del_catalogo(self):
        g = construir_k1(PELICULAS, {0: usuario("Drama", ["M1", "NO_EXISTE"])})
        self.assertEqual(g.conteo()["aristas"][ARISTA_VISTA], 1)
        self.assertNotIn(nodo_pelicula("NO_EXISTE"), g.nodos)


class TestConexionesUsuarios(unittest.TestCase):

    def test_solo_por_genero(self):
        g = construir_k1(PELICULAS, {0: usuario("Drama", ["M1"]), 1: usuario("Drama", ["M2"])})
        arista = g.arista(nodo_usuario(0), nodo_usuario(1))
        self.assertEqual(arista["motivos"], [MOTIVO_GENERO])
        self.assertEqual(arista["comunes"], [])

    def test_solo_por_peliculas_en_comun(self):
        g = construir_k1(PELICULAS, {0: usuario("Drama", ["M1", "M3"]), 1: usuario("Terror", ["M3", "M4"])})
        arista = g.arista(nodo_usuario(0), nodo_usuario(1))
        self.assertEqual(arista["motivos"], [MOTIVO_PELICULAS])
        self.assertEqual(arista["comunes"], ["M3"])

    def test_por_ambos_motivos(self):
        g = construir_k1(PELICULAS, {0: usuario("Drama", ["M1", "M2"]), 1: usuario("Drama", ["M1", "M2"])})
        arista = g.arista(nodo_usuario(0), nodo_usuario(1))
        self.assertEqual(arista["motivos"], [MOTIVO_GENERO, MOTIVO_PELICULAS])
        self.assertEqual(arista["comunes"], ["M1", "M2"])

    def test_sin_motivos_no_hay_arista(self):
        g = construir_k1(PELICULAS, {0: usuario("Drama", ["M1"]), 1: usuario("Terror", ["M3"])})
        self.assertIsNone(g.arista(nodo_usuario(0), nodo_usuario(1)))
        self.assertEqual(g.usuarios_conectados(0), [])

    def test_usuarios_sin_genero_no_se_conectan(self):
        # Antes: None == None los unía a todos. Ahora no.
        g = construir_k1(PELICULAS, {0: usuario(None, []), 1: usuario(None, []), 2: usuario(None, [])})
        self.assertEqual(g.conteo()["aristas"][ARISTA_USUARIO], 0)
        self.assertEqual(motivos_conexion(None, None, []), [])

    def test_sin_genero_frente_a_usuario_con_genero(self):
        g = construir_k1(PELICULAS, {0: usuario(None, []), 1: usuario("Drama", ["M1"])})
        self.assertIsNone(g.arista(nodo_usuario(0), nodo_usuario(1)))

    def test_umbral_de_peliculas_comunes(self):
        usuarios = {0: usuario("Drama", ["M1", "M3"]), 1: usuario("Terror", ["M3", "M4"])}
        self.assertIsNotNone(construir_grafo(PELICULAS, usuarios, min_comunes=1).arista(nodo_usuario(0), nodo_usuario(1)))
        self.assertIsNone(construir_grafo(PELICULAS, usuarios, min_comunes=2).arista(nodo_usuario(0), nodo_usuario(1)))
        with self.assertRaises(ValueError):
            construir_grafo(PELICULAS, usuarios, min_comunes=0)

    def test_umbral_por_defecto_es_3(self):
        # Elegido tras medir (docs/medicion_k.md): con 2 en común no se conectan, con 3 sí
        self.assertEqual(MIN_PELICULAS_COMUNES, 3)
        dos = {0: usuario("Drama", ["M1", "M2"]), 1: usuario("Terror", ["M1", "M2", "M4"])}
        tres = {0: usuario("Drama", ["M1", "M2", "M3"]), 1: usuario("Terror", ["M1", "M2", "M3"])}
        self.assertIsNone(construir_grafo(PELICULAS, dos).arista(nodo_usuario(0), nodo_usuario(1)))
        arista = construir_grafo(PELICULAS, tres).arista(nodo_usuario(0), nodo_usuario(1))
        self.assertEqual(arista["motivos"], [MOTIVO_PELICULAS])
        self.assertEqual(arista["comunes"], ["M1", "M2", "M3"])

    def test_vista_de_usuarios_es_simetrica(self):
        usuarios = {0: usuario("Drama", ["M1"]), 1: usuario("Drama", ["M2"]), 2: usuario("Terror", ["M1"])}
        g = construir_k1(PELICULAS, usuarios)
        self.assertEqual(sorted(g.usuarios_conectados(0)), [1, 2])
        for u in usuarios:
            for v in g.usuarios_conectados(u):
                self.assertIn(u, g.usuarios_conectados(v))


class TestConteo(unittest.TestCase):

    def test_conteo_por_tipo(self):
        usuarios = {0: usuario("Drama", ["M1", "M2"]), 1: usuario("Drama", ["M2"]), 2: usuario(None, [])}
        conteo = construir_k1(PELICULAS, usuarios).conteo()
        self.assertEqual(conteo["vertices"], {"usuario": 3, "pelicula": 4, "total": 7})
        # 3 vistas + 1 arista usuario-usuario (0-1, por género y M2)
        self.assertEqual(conteo["aristas"], {"vista": 3, "usuario": 1, "total": 4})

    def test_sin_aristas_duplicadas(self):
        g = construir_k1(PELICULAS, {0: usuario("Drama", ["M1", "M1"]), 1: usuario("Drama", ["M1"])})
        total_extremos = sum(len(v) for v in g.adyacencia.values())
        self.assertEqual(total_extremos, 2 * g.conteo()["aristas"]["total"])

    def test_determinista(self):
        usuarios = {i: usuario(["Drama", "Terror", None][i % 3], ["M1", "M3"][: i % 3]) for i in range(6)}
        self.assertEqual(construir_k1(PELICULAS, usuarios).aristas, construir_k1(PELICULAS, usuarios).aristas)

    def test_catalogo_real_1500_peliculas(self):
        ruta = os.path.join(CARPETA_BACKEND, "peliculas_streaming_1000.csv")
        with open(ruta, encoding="utf-8-sig", newline="") as archivo:
            peliculas = list(csv.DictReader(archivo))
        usuarios = {0: usuario("Drama", [peliculas[0]["movie_id"]]), 1: usuario(None, [])}
        conteo = construir_k1(peliculas, usuarios).conteo()
        self.assertEqual(conteo["vertices"]["pelicula"], len(peliculas))
        self.assertEqual(conteo["vertices"]["pelicula"], 1500)
        self.assertEqual(conteo["vertices"]["total"], 1502)


class TestUsuario(unittest.TestCase):

    def test_sin_vistas_el_genero_favorito_es_none(self):
        u = Usuario("Ana", "Pérez", "a@example.com", 0)
        u.genero_preferido = "Drama"  # valor anterior
        u.obtener_generos_vistos()
        self.assertIsNone(u.get_generoFav())


if __name__ == "__main__":
    unittest.main()
