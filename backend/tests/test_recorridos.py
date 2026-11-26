"""Pruebas de BFS y DFS (solo biblioteca estándar).

Grafo base (min_comunes = 1):

    películas: M1 M2 M3 (Drama)   M4 M5 M6 (Terror)
    usuario 0  Drama   vio M1 M2
    usuario 1  Terror  vio M2 M4     0-1 por película común (M2)
    usuario 2  Terror  vio M5        1-2 por género
    usuario 3  sin vistas (None)     aislado

    Vista de usuarios:  0 — 1 — 2      3

Grafo con ramas (para distinguir BFS de DFS):

    usuario 0 Drama  [M1]      0-1 género, 0-2 por M1
    usuario 1 Drama  [M4]      1-3 por M4
    usuario 2 Terror [M1]      2-3 género
    usuario 3 Terror [M4]

          1
        /   \\
      0       3        BFS desde 0: 0, 1, 2, 3
        \\   /         DFS desde 0: 0, 1, 3, 2
          2
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
    componentes_usuarios,
    dfs,
    ranking_generos,
    recomendar_bfs,
    recomendar_por_generos,
    reconstruir_camino,
    recorrido_pasos,
    resumen_componentes,
)


def construir_k1(peliculas, usuarios):
    """Grafos de prueba pequeños: basta 1 película en común para conectar."""
    return construir_grafo(peliculas, usuarios, min_comunes=1)

PELICULAS = [{"movie_id": f"M{i}", "genero": "Drama" if i <= 3 else "Terror"} for i in range(1, 7)]
U, P = nodo_usuario, nodo_pelicula


def usuario(genero, vistas):
    return {"nombre": "x", "genero_favorito": genero, "vistas": vistas}


def grafo_base():
    return construir_k1(PELICULAS, {
        0: usuario("Drama", ["M1", "M2"]),
        1: usuario("Terror", ["M2", "M4"]),
        2: usuario("Terror", ["M5"]),
        3: usuario(None, []),
    })


def grafo_ramas():
    return construir_k1(PELICULAS, {
        0: usuario("Drama", ["M1"]),
        1: usuario("Drama", ["M4"]),
        2: usuario("Terror", ["M1"]),
        3: usuario("Terror", ["M4"]),
    })


class TestBFS(unittest.TestCase):

    def test_niveles_y_padres(self):
        path, nivel = bfs(grafo_base(), U(0))
        self.assertIsNone(path[U(0)])
        self.assertEqual(nivel[U(0)], 0)
        self.assertEqual(nivel[P("M1")], 1)
        self.assertEqual(nivel[U(1)], 1)        # arista usuario-usuario
        self.assertEqual(nivel[U(2)], 2)
        self.assertEqual(path[U(2)], U(1))
        self.assertEqual(nivel[P("M5")], 3)
        self.assertNotIn(U(3), path)            # inalcanzable
        self.assertNotIn(P("M3"), path)         # nadie la vio

    def test_orden_por_niveles(self):
        path, _ = bfs(grafo_ramas(), U(0), ARISTA_USUARIO)
        self.assertEqual(list(path), [U(0), U(1), U(2), U(3)])

    def test_filtro_por_tipo_de_arista(self):
        _, nivel = bfs(grafo_base(), U(0), ARISTA_VISTA)
        self.assertEqual(nivel[U(1)], 2)        # solo vía M2
        self.assertNotIn(U(2), nivel)           # 1-2 es solo por género

    def test_max_nivel(self):
        _, nivel = bfs(grafo_base(), U(0), max_nivel=1)
        self.assertEqual(max(nivel.values()), 1)  # los del nivel 1 se descubren pero no se expanden
        _, nivel = bfs(grafo_base(), U(0), max_nivel=0)
        self.assertEqual(list(nivel), [U(0)])

    def test_pasos_con_estado_de_la_cola(self):
        pasos = []
        bfs(grafo_ramas(), U(0), ARISTA_USUARIO, pasos=pasos)
        self.assertEqual(
            [(p["nodo"], p["padre"], p["estructura"]) for p in pasos],
            [(U(0), None, [U(1), U(2)]),
             (U(1), U(0), [U(2), U(3)]),
             (U(2), U(0), [U(3)]),
             (U(3), U(1), [])],
        )

    def test_reconstruir_camino(self):
        path, _ = bfs(grafo_base(), U(0))
        self.assertEqual(reconstruir_camino(path, P("M5")), [U(0), U(1), U(2), P("M5")])
        self.assertEqual(reconstruir_camino(path, U(3)), [])

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
        g = construir_k1(PELICULAS, {
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


class TestRecomendarBFS(unittest.TestCase):
    """Usuario 0 (Drama) vio M1 M2 M3. Películas en común con él:
    u1 = 2 (M1 M2), u2 = 1 (M3), u3 = 1 (M1), u4 = 1 (M3).
    Candidatas: M4 (u1, u3) = 2 + 1 = 3; M5 (u2, u3) = 2; M6 (u3) = 1 Terror; M7 (u4) = 1 Drama.
    """
    CATALOGO = PELICULAS + [{"movie_id": "M7", "genero": "Drama"}]

    def grafo(self):
        return construir_k1(self.CATALOGO, {
            0: usuario("Drama", ["M1", "M2", "M3"]),
            1: usuario("Terror", ["M1", "M2", "M4"]),
            2: usuario("Terror", ["M3", "M5"]),
            3: usuario("Terror", ["M1", "M4", "M5", "M6"]),
            4: usuario("Drama", ["M3", "M7"]),
            5: usuario(None, []),
        })

    def test_puntaje_y_orden(self):
        recs = recomendar_bfs(self.grafo(), 0, n=5)
        self.assertEqual([(r["movie_id"], r["puntaje"]) for r in recs],
                         [("M4", 3), ("M5", 2), ("M7", 1), ("M6", 1)])  # M7 antes que M6: mismo género que el usuario
        self.assertTrue(all(r["origen"] == "bfs" for r in recs))
        self.assertEqual(recs[0]["usuarios"], [1, 3])

    def test_no_recomienda_vistas_y_es_determinista(self):
        g = self.grafo()
        recs = recomendar_bfs(g, 0, n=5)
        self.assertFalse({r["movie_id"] for r in recs} & {"M1", "M2", "M3"})
        self.assertEqual(recs, recomendar_bfs(self.grafo(), 0, n=5))

    def test_camino_valido(self):
        g = self.grafo()
        for r in recomendar_bfs(g, 0, n=5):
            camino = r["camino"]
            self.assertEqual(camino[0], U(0))
            self.assertEqual(camino[-1], P(r["movie_id"]))
            for a, b in zip(camino, camino[1:]):
                self.assertEqual(g.arista(a, b)["tipo"], ARISTA_VISTA)

    def test_limite_n(self):
        self.assertEqual([r["movie_id"] for r in recomendar_bfs(self.grafo(), 0, n=2)], ["M4", "M5"])

    def test_respaldo_por_popularidad(self):
        recs = recomendar_bfs(self.grafo(), 5, n=5)  # usuario sin vistas: el BFS no da candidatas
        self.assertEqual([(r["movie_id"], r["origen"], r["puntaje"]) for r in recs],
                         [("M1", "popularidad", 3), ("M3", "popularidad", 3), ("M2", "popularidad", 2),
                          ("M4", "popularidad", 2), ("M5", "popularidad", 2)])
        self.assertTrue(all(r["camino"] == [] for r in recs))

    def test_completa_con_popularidad_sin_repetir(self):
        g = self.grafo()
        recs = recomendar_bfs(g, 2, n=5)  # u2 vio M3 M5
        ids = [r["movie_id"] for r in recs]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertFalse(set(ids) & {"M3", "M5"})
        origenes = [r["origen"] for r in recs]
        self.assertEqual(origenes, sorted(origenes, key=lambda o: o != "bfs"))  # primero las del BFS


class TestRecomendarPorGeneros(unittest.TestCase):
    """Usuario 0: favorito Aventura (4 vistas), luego Terror (3) y Comedia (2).
    Cada género tiene 4 películas más que no vio; u1 vio todo el catálogo,
    así que todas son candidatas del BFS."""
    GENEROS = {"Aventura": 8, "Terror": 7, "Comedia": 6, "Drama": 5}

    def grafo(self, vistas_0=None):
        catalogo = [{"movie_id": f"{g[0]}{i}", "genero": g} for g, k in self.GENEROS.items() for i in range(k)]
        if vistas_0 is None:
            vistas_0 = [f"A{i}" for i in range(4)] + [f"T{i}" for i in range(3)] + [f"C{i}" for i in range(2)] + ["D0"]
        return construir_k1(catalogo, {
            0: usuario("Aventura", vistas_0),
            1: usuario("Aventura", [p["movie_id"] for p in catalogo]),
        })

    def generos(self, g, recs):
        return [g.nodos[P(r["movie_id"])]["genero"] for r in recs]

    def test_ranking(self):
        self.assertEqual(ranking_generos(self.grafo(), 0), ["Aventura", "Terror", "Comedia", "Drama"])

    def test_tres_del_favorito_y_luego_los_siguientes(self):
        g = self.grafo()
        recs = recomendar_por_generos(g, 0, n=5)
        self.assertEqual(self.generos(g, recs), ["Aventura"] * 3 + ["Terror", "Comedia"])
        self.assertTrue(all(r["origen"] == "bfs" for r in recs))
        self.assertEqual(len({r["movie_id"] for r in recs}), 5)

    def test_mas_huecos_que_generos_vuelve_al_segundo(self):
        g = self.grafo()
        recs = recomendar_por_generos(g, 0, n=8)
        self.assertEqual(self.generos(g, recs), ["Aventura"] * 3 + ["Terror", "Comedia", "Drama", "Terror", "Comedia"])

    def test_un_solo_genero(self):
        g = self.grafo(vistas_0=["A0", "A1"])
        self.assertEqual(self.generos(g, recomendar_por_generos(g, 0, n=5)), ["Aventura"] * 5)

    def test_sin_vistas_usa_popularidad(self):
        recs = recomendar_por_generos(self.grafo(vistas_0=[]), 0, n=5)
        self.assertEqual(len(recs), 5)
        self.assertTrue(all(r["origen"] == "popularidad" for r in recs))


class TestDFS(unittest.TestCase):

    def test_profundidad_primero(self):
        path = dfs(grafo_ramas(), U(0), ARISTA_USUARIO)
        self.assertEqual(list(path), [U(0), U(1), U(3), U(2)])
        self.assertEqual(path[U(2)], U(3))   # llegó a 2 bajando por 3, no desde 0

    def test_padres_forman_un_arbol(self):
        g = grafo_base()
        path = dfs(g, U(0))
        orden = list(path)
        posicion = {n: i for i, n in enumerate(orden)}
        for nodo in orden[1:]:
            self.assertIsNotNone(g.arista(nodo, path[nodo]))       # padre adyacente
            self.assertLess(posicion[path[nodo]], posicion[nodo])  # visitado antes

    def test_alcanza_lo_mismo_que_bfs(self):
        for g in (grafo_base(), grafo_ramas()):
            self.assertEqual(set(dfs(g, U(0))), set(bfs(g, U(0))[0]))

    def test_pasos_con_la_pila_de_llamadas(self):
        pasos = []
        dfs(grafo_ramas(), U(0), ARISTA_USUARIO, pasos=pasos)
        self.assertEqual(
            [(p["nodo"], p["padre"], p["estructura"]) for p in pasos],
            [(U(0), None, [U(0)]),
             (U(1), U(0), [U(0), U(1)]),
             (U(3), U(1), [U(0), U(1), U(3)]),
             (U(2), U(3), [U(0), U(1), U(3), U(2)])],
        )

    def test_componentes_de_usuarios(self):
        resultado = componentes_usuarios(grafo_base())
        self.assertEqual(resultado["componentes"], [[0, 1, 2], [3]])
        self.assertEqual(resultado["aislados"], [3])

    def test_resumen_componentes(self):
        self.assertEqual(resumen_componentes(grafo_base()),
                         {"componentes": 2, "mayor": 3, "aislados": 1, "peliculas_sin_vistas": 2})

    def test_sin_usuarios(self):
        g = construir_k1(PELICULAS, {})
        self.assertEqual(componentes_usuarios(g), {"componentes": [], "aislados": []})
        self.assertEqual(resumen_componentes(g)["peliculas_sin_vistas"], 6)


class TestRecorridoPasos(unittest.TestCase):

    def test_bfs_y_dfs_con_ids_de_usuario(self):
        bfs_r = recorrido_pasos(grafo_ramas(), "bfs", 0)
        dfs_r = recorrido_pasos(grafo_ramas(), "dfs", 0)
        self.assertEqual([p["nodo"] for p in bfs_r["pasos"]], [0, 1, 2, 3])
        self.assertEqual([p["nodo"] for p in dfs_r["pasos"]], [0, 1, 3, 2])
        self.assertEqual(bfs_r["pasos"][0], {"nodo": 0, "padre": None, "componente": 1, "estructura": [1, 2]})
        self.assertEqual(dfs_r["pasos"][2]["estructura"], [0, 1, 3])
        self.assertEqual(bfs_r["miembros"], [0, 1, 2, 3])
        self.assertEqual(set(bfs_r), {"tipo", "inicio", "componentes", "miembros", "pasos"})

    def test_solo_la_componente_del_inicio(self):
        r = recorrido_pasos(grafo_base(), "bfs", 0)
        self.assertEqual(r["miembros"], [0, 1, 2])
        self.assertEqual(r["componentes"], 1)

    def test_todo_cubre_todas_las_componentes(self):
        for tipo in ("bfs", "dfs"):
            r = recorrido_pasos(grafo_base(), tipo, 0, todo=True)
            self.assertEqual(r["componentes"], 2)
            self.assertEqual(r["miembros"], [0, 1, 2, 3])
            self.assertEqual(r["pasos"][-1], {"nodo": 3, "padre": None, "componente": 2,
                                              "estructura": [3] if tipo == "dfs" else []})

    def test_tipo_invalido(self):
        with self.assertRaises(ValueError):
            recorrido_pasos(grafo_base(), "xyz", 0)


if __name__ == "__main__":
    unittest.main()
