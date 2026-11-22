"""Pruebas de Kruskal + UFDS (mst.py), solo biblioteca estándar."""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from grafo import ARISTA_USUARIO, construir_grafo  # noqa: E402
from mst import Graph, bosque_expansion_minima, distancia_jaccard  # noqa: E402
from recorridos import componentes_usuarios  # noqa: E402

PELICULAS = [{"movie_id": f"M{i}", "genero": "Drama" if i <= 3 else "Terror"} for i in range(1, 7)]


def usuario(genero, vistas):
    return {"nombre": "x", "genero_favorito": genero, "vistas": vistas}


def grafo_notebook():
    """Grafo de 6 nodos del notebook MST_Algoritmo_Kruskal, una vez por arista."""
    g = Graph(6)
    for u, v, w in [(0, 1, 4), (0, 2, 4), (1, 2, 2), (2, 3, 3), (2, 5, 2), (2, 4, 4), (3, 4, 3), (4, 5, 3)]:
        g.addEdge(u, v, w)
    return g


def sin_ciclos(V, aristas):
    """Comprueba con el mismo find/applyUnion que ninguna arista cierra un ciclo."""
    g = Graph(V)
    parent, rank = list(range(V)), [0] * V
    for u, v, _ in aristas:
        x, y = g.find(parent, u), g.find(parent, v)
        if x == y:
            return False
        g.applyUnion(parent, rank, x, y)
    return True


class TestUFDS(unittest.TestCase):

    def test_find_recursivo(self):
        g = Graph(4)
        parent = [0, 0, 1, 3]  # 2 -> 1 -> 0
        self.assertEqual(g.find(parent, 2), 0)
        self.assertEqual(g.find(parent, 3), 3)

    def test_union_por_rango(self):
        g = Graph(4)
        parent, rank = [0, 1, 2, 3], [0, 0, 0, 0]
        g.applyUnion(parent, rank, 0, 1)        # mismo rango: 1 cuelga de 0 y sube el rango de 0
        self.assertEqual((parent, rank), ([0, 0, 2, 3], [1, 0, 0, 0]))
        g.applyUnion(parent, rank, 2, 0)        # rango 0 < 1: la raíz 2 cuelga de 0
        self.assertEqual((parent, rank), ([0, 0, 0, 3], [1, 0, 0, 0]))


class TestKruskal(unittest.TestCase):

    def test_grafo_del_notebook(self):
        result, total = grafo_notebook().kruskalMST()
        self.assertEqual(total, 14)
        self.assertEqual(len(result), 5)        # V - 1 aristas
        self.assertTrue(sin_ciclos(6, result))

    def test_grafo_disconexo_da_un_bosque(self):
        g = Graph(5)                            # componentes {0,1}, {2,3} y el vértice 4 aislado
        g.addEdge(0, 1, 1)
        g.addEdge(2, 3, 2)
        result, total = g.kruskalMST()          # sin IndexError
        self.assertEqual(result, [[0, 1, 1], [2, 3, 2]])
        self.assertEqual(total, 3)
        self.assertEqual(5 - len(result), 3)    # 3 árboles

    def test_sin_aristas(self):
        self.assertEqual(Graph(3).kruskalMST(), ([], 0))


class TestBosqueUsuarios(unittest.TestCase):

    def grafo(self):
        # 0-1 por género y M1 M2; 1-2 por M2; 0-2 por género Drama; 3 aislado (sin vistas)
        return construir_grafo(PELICULAS, {
            0: usuario("Drama", ["M1", "M2", "M3"]),
            1: usuario("Drama", ["M1", "M2", "M4"]),
            2: usuario("Drama", ["M2", "M5"]),
            3: usuario(None, []),
        }, min_comunes=1)

    def test_distancia_jaccard(self):
        self.assertAlmostEqual(distancia_jaccard({"M1", "M2", "M3"}, {"M1", "M2", "M4"}), 1 - 2 / 4)
        self.assertAlmostEqual(distancia_jaccard({"M1", "M2", "M4"}, {"M2", "M5"}), 1 - 1 / 4)
        self.assertEqual(distancia_jaccard({"M1"}, {"M1"}), 0)
        self.assertEqual(distancia_jaccard({"M1"}, {"M2"}), 1)
        self.assertEqual(distancia_jaccard(set(), set()), 1.0)

    def test_bosque_de_maxima_similitud(self):
        b = bosque_expansion_minima(self.grafo())
        self.assertEqual(b["aristas_grafo"], 3)  # cada arista no dirigida una sola vez
        pares = [(a["source"], a["target"]) for a in b["aristas"]]
        self.assertEqual(pares[0], (0, 1))       # la de menor distancia (más parecidos) primero
        self.assertEqual(len(pares), 2)
        self.assertAlmostEqual(b["costo_total"], 0.5 + 0.75)
        self.assertEqual(b["arboles"], 2)        # {0,1,2} y el aislado 3

    def test_arboles_igual_componentes_dfs(self):
        grafos = [self.grafo(),
                  construir_grafo(PELICULAS, {i: usuario(["Drama", "Terror", None][i % 3], ["M1", "M4"][: i % 3])
                                              for i in range(7)}, min_comunes=1)]
        for g in grafos:
            b = bosque_expansion_minima(g)
            self.assertEqual(b["arboles"], len(componentes_usuarios(g)["componentes"]))
            aristas_usuario = sum(1 for a in g.aristas.values() if a["tipo"] == ARISTA_USUARIO)
            self.assertEqual(b["aristas_grafo"], aristas_usuario)

    def test_sin_usuarios(self):
        b = bosque_expansion_minima(construir_grafo(PELICULAS, {}))
        self.assertEqual((b["aristas"], b["arboles"], b["aristas_grafo"]), ([], 0, 0))


if __name__ == "__main__":
    unittest.main()
