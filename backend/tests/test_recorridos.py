"""Pruebas de BFS y DFS (solo biblioteca estándar).

Grafo de prueba (min_comunes = 1):

    películas: M1 M2 M3 (Drama)   M4 M5 M6 (Terror)
    usuario 0  Drama   vio M1 M2
    usuario 1  Terror  vio M2 M4     0-1 por película común (M2)
    usuario 2  Terror  vio M5        1-2 por género
    usuario 3  sin vistas (None)     aislado

    Vista de usuarios:  0 — 1 — 2      3
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from grafo import ARISTA_USUARIO, ARISTA_VISTA, construir_grafo, nodo_pelicula, nodo_usuario  # noqa: E402
from recorridos import (  # noqa: E402
    bfs,
    camino_entre_usuarios,
    candidatos_bfs,
    componentes_conexas,
    componentes_usuarios,
    dfs,
    reconstruir_camino,
    resumen_componentes,
)

PELICULAS = [{"movie_id": f"M{i}", "genero": "Drama" if i <= 3 else "Terror"} for i in range(1, 7)]
U, P = nodo_usuario, nodo_pelicula


def usuario(genero, vistas):
    return {"nombre": "x", "genero_favorito": genero, "vistas": vistas}


def grafo_base():
    return construir_grafo(PELICULAS, {
        0: usuario("Drama", ["M1", "M2"]),
        1: usuario("Terror", ["M2", "M4"]),
        2: usuario("Terror", ["M5"]),
        3: usuario(None, []),
    })


class TestBFS(unittest.TestCase):

    def test_distancias_por_niveles(self):
        distancia, padre, orden = bfs(grafo_base(), U(0))
        self.assertEqual(distancia[U(0)], 0)
        self.assertEqual(distancia[P("M1")], 1)
        self.assertEqual(distancia[U(1)], 1)        # arista usuario-usuario
        self.assertEqual(distancia[P("M4")], 2)
        self.assertEqual(distancia[U(2)], 2)
        self.assertEqual(distancia[P("M5")], 3)
        self.assertNotIn(U(3), distancia)           # inalcanzable
        self.assertNotIn(P("M3"), distancia)        # nadie la vio
        self.assertEqual(orden[0], U(0))
        self.assertIsNone(padre[U(0)])

    def test_niveles_no_decrecen_en_el_orden(self):
        distancia, _, orden = bfs(grafo_base(), U(0))
        niveles = [distancia[n] for n in orden]
        self.assertEqual(niveles, sorted(niveles))

    def test_filtro_por_tipo_de_arista(self):
        distancia, _, _ = bfs(grafo_base(), U(0), tipos_arista={ARISTA_VISTA})
        self.assertEqual(distancia[U(1)], 2)        # ahora solo vía M2
        self.assertNotIn(U(2), distancia)           # 1-2 es solo por género

    def test_max_nivel(self):
        distancia, _, _ = bfs(grafo_base(), U(0), max_nivel=1)
        self.assertEqual(max(distancia.values()), 1)

    def test_reconstruir_camino(self):
        _, padre, _ = bfs(grafo_base(), U(0))
        self.assertEqual(reconstruir_camino(padre, P("M5")), [U(0), U(1), U(2), P("M5")])
        self.assertEqual(reconstruir_camino(padre, U(3)), [])

    def test_camino_entre_usuarios(self):
        g = grafo_base()
        self.assertEqual(camino_entre_usuarios(g, 0, 2), [U(0), U(1), U(2)])
        self.assertEqual(camino_entre_usuarios(g, 0, 0), [U(0)])
        self.assertEqual(camino_entre_usuarios(g, 0, 3), [])


class TestCandidatosBFS(unittest.TestCase):

    def test_recorrido_usuario_pelicula_usuario_pelicula(self):
        candidatas = candidatos_bfs(grafo_base(), 0)
        self.assertEqual([c["movie_id"] for c in candidatas], ["M4"])
        self.assertEqual(candidatas[0]["usuarios"], [1])
        self.assertEqual(candidatas[0]["camino"], [U(0), P("M2"), U(1), P("M4")])

    def test_no_recomienda_peliculas_vistas(self):
        for id_usuario, vistas in ((0, {"M1", "M2"}), (1, {"M2", "M4"})):
            ids = {c["movie_id"] for c in candidatos_bfs(grafo_base(), id_usuario)}
            self.assertFalse(ids & vistas)

    def test_el_genero_no_sustituye_al_recorrido(self):
        ids = {c["movie_id"] for c in candidatos_bfs(grafo_base(), 0)}
        self.assertNotIn("M3", ids)  # mismo género que el usuario 0, pero nadie la vio
        self.assertNotIn("M5", ids)  # el usuario 2 se une al 1 solo por género

    def test_usuario_sin_vistas_no_tiene_candidatas(self):
        self.assertEqual(candidatos_bfs(grafo_base(), 3), [])

    def test_orden_por_cantidad_de_usuarios(self):
        g = construir_grafo(PELICULAS, {
            0: usuario("Drama", ["M1", "M2"]),
            1: usuario("Terror", ["M1", "M4", "M5"]),
            2: usuario("Terror", ["M2", "M4"]),
        })
        candidatas = candidatos_bfs(g, 0)
        self.assertEqual([c["movie_id"] for c in candidatas], ["M4", "M5"])
        self.assertEqual(candidatas[0]["usuarios"], [1, 2])
        for c in candidatas:
            camino = c["camino"]
            self.assertEqual(len(camino), 4)
            for a, b in zip(camino, camino[1:]):
                self.assertEqual(g.arista(a, b)["tipo"], ARISTA_VISTA)


class TestDFS(unittest.TestCase):

    def test_orden_y_padres_forman_un_arbol(self):
        g = grafo_base()
        orden, padre = dfs(g, U(0))
        self.assertEqual(orden[0], U(0))
        self.assertEqual(len(orden), len(set(orden)))
        posicion = {n: i for i, n in enumerate(orden)}
        for nodo in orden[1:]:
            self.assertIsNotNone(g.arista(nodo, padre[nodo]))       # padre adyacente
            self.assertLess(posicion[padre[nodo]], posicion[nodo])  # visitado antes

    def test_alcanza_lo_mismo_que_bfs(self):
        g = grafo_base()
        orden, _ = dfs(g, U(0))
        distancia, _, _ = bfs(g, U(0))
        self.assertEqual(set(orden), set(distancia))

    def test_profundidad_primero(self):
        # Cadena 0 - 1 - 2 por aristas usuario: DFS llega a 2 antes de volver
        orden, _ = dfs(grafo_base(), U(0), tipos_arista={ARISTA_USUARIO})
        self.assertEqual(orden, [U(0), U(1), U(2)])

    def test_componentes_de_usuarios(self):
        resultado = componentes_usuarios(grafo_base())
        self.assertEqual(resultado["componentes"], [[0, 1, 2], [3]])
        self.assertEqual(resultado["aislados"], [3])

    def test_componentes_del_grafo_completo(self):
        componentes = componentes_conexas(grafo_base())
        self.assertEqual(len(componentes), 4)       # grande + M3 + M6 + U:3
        self.assertEqual(len(componentes[0]), 7)
        self.assertEqual(sum(len(c) for c in componentes), 10)

    def test_resumen_componentes(self):
        resumen = resumen_componentes(grafo_base())
        self.assertEqual(resumen["grafo_completo"], {"componentes": 4, "mayor": 7, "peliculas_sin_vistas": 2})
        self.assertEqual(resumen["usuarios"], {"componentes": 2, "mayor": 3, "aislados": 1})

    def test_sin_usuarios_cada_pelicula_es_una_componente(self):
        g = construir_grafo(PELICULAS, {})
        self.assertEqual(len(componentes_conexas(g)), 6)
        self.assertEqual(componentes_usuarios(g), {"componentes": [], "aislados": []})


if __name__ == "__main__":
    unittest.main()
