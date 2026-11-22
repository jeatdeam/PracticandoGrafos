"""Pruebas de la validación (evaluar.py), solo biblioteca estándar."""
import os
import random
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from evaluar import (  # noqa: E402
    evaluar,
    genero_favorito,
    precision_recall,
    rec_aleatorio,
    rec_genero,
    rec_popularidad,
    separar_vistas,
)
from grafo import construir_grafo, nodo_pelicula, nodo_usuario  # noqa: E402

PELICULAS = [{"movie_id": f"M{i}", "genero": "Drama" if i <= 5 else "Terror"} for i in range(1, 11)]
CATALOGO = [p["movie_id"] for p in PELICULAS]
GENERO = {p["movie_id"]: p["genero"] for p in PELICULAS}


class TestSeparacion(unittest.TestCase):

    def test_entrenamiento_y_prueba_no_se_mezclan(self):
        vistas = {0: CATALOGO[:10], 1: CATALOGO[:4], 2: []}
        entrenamiento, prueba = separar_vistas(vistas, 0.2, semilla=1)
        for u in vistas:
            self.assertFalse(set(entrenamiento[u]) & set(prueba[u]))
            self.assertEqual(sorted(entrenamiento[u] + prueba[u]), sorted(vistas[u]))
        self.assertEqual(len(prueba[0]), 2)   # int(0.2 * 10)
        self.assertEqual(len(prueba[1]), 0)   # int(0.2 * 4) = 0: queda fuera de la evaluación
        self.assertEqual(prueba[2], [])

    def test_determinista(self):
        vistas = {0: CATALOGO, 1: CATALOGO[2:]}
        self.assertEqual(separar_vistas(vistas, 0.2, 7), separar_vistas(vistas, 0.2, 7))

    def test_grafo_de_entrenamiento_sin_aristas_de_prueba(self):
        vistas = {0: CATALOGO[:10], 1: CATALOGO[3:8]}
        entrenamiento, prueba = separar_vistas(vistas, 0.2, 3)
        usuarios = {u: {"nombre": "x", "genero_favorito": genero_favorito(entrenamiento[u], GENERO),
                        "vistas": entrenamiento[u]} for u in vistas}
        grafo = construir_grafo(PELICULAS, usuarios)
        for u in vistas:
            for m in prueba[u]:
                self.assertIsNone(grafo.arista(nodo_usuario(u), nodo_pelicula(m)))


class TestMetricasYRecomendadores(unittest.TestCase):

    def test_precision_recall(self):
        self.assertEqual(precision_recall(["M1", "M2", "M3", "M4", "M5"], ["M2", "M9"], 5), (1 / 5, 1 / 2, 1))
        self.assertEqual(precision_recall(["M1"], ["M2"], 5), (0.0, 0.0, 0))

    def test_genero_favorito(self):
        self.assertEqual(genero_favorito(["M1", "M2", "M6"], GENERO), "Drama")
        self.assertIsNone(genero_favorito([], GENERO))

    def test_no_recomiendan_vistas_de_entrenamiento(self):
        vistas = ["M1", "M2", "M6"]
        conteo = {"M1": 9, "M3": 5, "M7": 5, "M2": 1}
        self.assertEqual(rec_popularidad(vistas, CATALOGO, conteo, 3), ["M3", "M7", "M10"])
        self.assertEqual(rec_genero(vistas, CATALOGO, GENERO, "Drama", 5), ["M3", "M4", "M5"])
        self.assertEqual(rec_genero(vistas, CATALOGO, GENERO, None, 5), [])
        aleatorias = rec_aleatorio(vistas, CATALOGO, random.Random(0), 5)
        self.assertEqual(len(aleatorias), 5)
        self.assertFalse(set(aleatorias) & set(vistas))


class TestEvaluar(unittest.TestCase):

    def test_bfs_acierta_cuando_hay_estructura(self):
        # El usuario 1 vio M1..M5; el 0 vio M1..M4 en entrenamiento y M5 queda en prueba.
        # El BFS (u0 -> M1 -> u1 -> M5) debe recomendar M5 y acertar.
        vistas = {0: ["M1", "M2", "M3", "M4", "M5"], 1: ["M1", "M2", "M3", "M4", "M5"]}
        resultado = evaluar(PELICULAS, vistas, n=1, proporcion=0.2, semilla=0)
        self.assertEqual(resultado["usuarios_evaluados"], 2)
        self.assertEqual(resultado["metodos"]["bfs"]["precision"], 1.0)
        self.assertEqual(resultado["metodos"]["bfs"]["recall"], 1.0)
        self.assertEqual(set(resultado["metodos"]), {"bfs", "aleatorio", "popularidad", "genero"})

    def test_usuarios_sin_prueba_se_informan(self):
        vistas = {0: CATALOGO[:10], 1: ["M1", "M2"], 2: []}
        resultado = evaluar(PELICULAS, vistas, n=5, proporcion=0.2, semilla=0)
        self.assertEqual(resultado["usuarios_evaluados"], 1)
        self.assertEqual(resultado["usuarios_sin_prueba"], 2)
        for m in resultado["metodos"].values():
            self.assertTrue(0 <= m["precision"] <= 1 and 0 <= m["recall"] <= 1)


if __name__ == "__main__":
    unittest.main()
