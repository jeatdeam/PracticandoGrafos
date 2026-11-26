"""Pruebas de las recomendaciones por director, actor y popularidad (solo biblioteca estándar).

Catálogo de prueba:

    M1 Nolan    [Ana, Beto]       M4 Nolan   [Ana]
    M2 Nolan    [Beto]            M5 Gerwig  [Ana, Ciro]
    M3 Gerwig   [Ciro]            M6 Gerwig  [Beto]

    usuario 0 vio M1 M2 M3   -> director favorito Nolan (2), actor favorito Beto (2)
    usuario 1 vio M4 M5      -> hace que M4 y M5 sean las más populares sin ver por 0
    usuario 2 vio M5
    usuario 3 sin vistas
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from grafo import construir_grafo, separar_actores  # noqa: E402
from recorridos import (  # noqa: E402
    favorito_por_atributo,
    recomendar_populares,
    recomendar_por_atributo,
)

PELICULAS = [
    {"movie_id": "M1", "genero": "Drama", "director": "Nolan", "actores": "Ana, Beto"},
    {"movie_id": "M2", "genero": "Drama", "director": "Nolan", "actores": "Beto"},
    {"movie_id": "M3", "genero": "Drama", "director": "Gerwig", "actores": "Ciro"},
    {"movie_id": "M4", "genero": "Terror", "director": "Nolan", "actores": "Ana"},
    {"movie_id": "M5", "genero": "Terror", "director": "Gerwig", "actores": "Ana, Ciro"},
    {"movie_id": "M6", "genero": "Terror", "director": "Gerwig", "actores": "Beto"},
]


def usuario(vistas):
    return {"nombre": "x", "genero_favorito": None, "vistas": vistas}


def grafo():
    return construir_grafo(PELICULAS, {
        0: usuario(["M1", "M2", "M3"]),
        1: usuario(["M4", "M5"]),
        2: usuario(["M5"]),
        3: usuario([]),
    }, min_comunes=1)


def ids(recomendaciones):
    return [r["movie_id"] for r in recomendaciones]


class TestAtributosDelGrafo(unittest.TestCase):

    def test_separar_actores(self):
        self.assertEqual(separar_actores("Pedro Pascal, Ana de Armas"), ["Pedro Pascal", "Ana de Armas"])
        self.assertEqual(separar_actores(None), [])
        self.assertEqual(separar_actores(float("nan")), [])

    def test_nodo_pelicula_guarda_director_y_actores(self):
        nodo = grafo().nodos["P:M1"]
        self.assertEqual(nodo["director"], "Nolan")
        self.assertEqual(nodo["actores"], ["Ana", "Beto"])


class TestFavorito(unittest.TestCase):

    def test_director_y_actor_mas_vistos(self):
        g = grafo()
        self.assertEqual(favorito_por_atributo(g, 0, "director"), ("Nolan", 2))
        self.assertEqual(favorito_por_atributo(g, 0, "actores"), ("Beto", 2))

    def test_empate_se_resuelve_alfabeticamente(self):
        # Usuario 1: Nolan 1 vez y Gerwig 1 vez -> Gerwig; Ana 2 veces -> Ana
        g = grafo()
        self.assertEqual(favorito_por_atributo(g, 1, "director"), ("Gerwig", 1))
        self.assertEqual(favorito_por_atributo(g, 1, "actores"), ("Ana", 2))

    def test_sin_vistas(self):
        self.assertEqual(favorito_por_atributo(grafo(), 3, "director"), (None, 0))


class TestRecomendarPorAtributo(unittest.TestCase):

    def test_por_director_solo_no_vistas_del_favorito(self):
        r = recomendar_por_atributo(grafo(), 0, "director")
        self.assertEqual(r["favorito"], "Nolan")
        self.assertEqual(r["vistas_del_favorito"], 2)
        self.assertEqual(ids(r["recomendaciones"]), ["M4"])
        self.assertEqual(r["recomendaciones"][0]["origen"], "director")

    def test_por_actor_ordena_por_popularidad(self):
        # Beto aparece en M6 (no vista por nadie); para Ana probamos con el usuario 1
        r = recomendar_por_atributo(grafo(), 0, "actores")
        self.assertEqual((r["favorito"], ids(r["recomendaciones"])), ("Beto", ["M6"]))
        self.assertEqual(r["recomendaciones"][0]["origen"], "actor")
        r = recomendar_por_atributo(grafo(), 1, "actores")
        self.assertEqual(ids(r["recomendaciones"]), ["M1"])  # Ana: M1 (1 vista); M4 y M5 ya las vio

    def test_respeta_n(self):
        r = recomendar_por_atributo(grafo(), 2, "director", n=1)  # Gerwig: M3 (1 vista) antes que M6 (0)
        self.assertEqual(ids(r["recomendaciones"]), ["M3"])
        self.assertEqual(r["recomendaciones"][0]["puntaje"], 1)

    def test_sin_vistas_no_recomienda(self):
        r = recomendar_por_atributo(grafo(), 3, "director")
        self.assertEqual(r, {"favorito": None, "vistas_del_favorito": 0, "recomendaciones": []})

    def test_atributo_invalido(self):
        with self.assertRaises(ValueError):
            recomendar_por_atributo(grafo(), 0, "genero")


class TestPopulares(unittest.TestCase):

    def test_mas_vistas_que_no_vio(self):
        r = recomendar_populares(grafo(), 0, n=3)
        self.assertEqual(ids(r), ["M5", "M4", "M6"])  # M5: 2 vistas, M4: 1, M6: 0
        self.assertEqual([x["puntaje"] for x in r], [2, 1, 0])
        self.assertTrue(all(x["origen"] == "popularidad" for x in r))

    def test_excluir(self):
        self.assertEqual(ids(recomendar_populares(grafo(), 0, n=2, excluir={"M5"})), ["M4", "M6"])


if __name__ == "__main__":
    unittest.main()
