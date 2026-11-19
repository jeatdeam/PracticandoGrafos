"""Recorridos BFS y DFS sobre el grafo único (grafo.py).

Implementados explícitamente, como en clase:
    BFS: cola FIFO, visitados, padres y distancia por niveles.   O(V + E)
    DFS: pila explícita (iterativo), visitados y padres.         O(V + E)

Los filtros por tipo de nodo o de arista permiten recorrer una "vista" del
mismo grafo (por ejemplo, solo usuarios conectados entre sí) sin construir
un grafo aparte.
"""
from collections import deque

from grafo import ARISTA_USUARIO, ARISTA_VISTA, TIPO_PELICULA, TIPO_USUARIO, clave_arista, nodo_usuario


def _vecinos_filtrados(grafo, nodo, tipos_arista, tipos_nodo):
    for v in grafo.adyacencia[nodo]:
        if tipos_arista is not None and grafo.aristas[clave_arista(nodo, v)]["tipo"] not in tipos_arista:
            continue
        if tipos_nodo is not None and grafo.nodos[v]["tipo"] not in tipos_nodo:
            continue
        yield v


# ----------------------------------- BFS -----------------------------------

def bfs(grafo, origen, tipos_arista=None, tipos_nodo=None, max_nivel=None):
    """Recorrido en anchura desde `origen`.

    Devuelve (distancia, padre, orden):
        distancia[n]  nivel en el que se descubrió n (origen = 0)
        padre[n]      nodo desde el que se descubrió n (origen -> None)
        orden         nodos en el orden en que salieron de la cola
    Con max_nivel no se expanden nodos de ese nivel en adelante.
    """
    distancia = {origen: 0}
    padre = {origen: None}
    orden = []
    cola = deque([origen])

    while cola:
        u = cola.popleft()
        orden.append(u)
        if max_nivel is not None and distancia[u] >= max_nivel:
            continue
        for v in _vecinos_filtrados(grafo, u, tipos_arista, tipos_nodo):
            if v not in distancia:  # no visitado
                distancia[v] = distancia[u] + 1
                padre[v] = u
                cola.append(v)

    return distancia, padre, orden


def reconstruir_camino(padre, destino):
    """Camino origen -> destino siguiendo los padres; [] si no se alcanzó."""
    if destino not in padre:
        return []
    camino = []
    nodo = destino
    while nodo is not None:
        camino.append(nodo)
        nodo = padre[nodo]
    camino.reverse()
    return camino


def camino_entre_usuarios(grafo, id_origen, id_destino):
    """Camino mínimo en saltos entre dos usuarios usando solo aristas usuario-usuario."""
    origen, destino = nodo_usuario(id_origen), nodo_usuario(id_destino)
    _, padre, _ = bfs(grafo, origen, tipos_arista={ARISTA_USUARIO}, tipos_nodo={TIPO_USUARIO})
    return reconstruir_camino(padre, destino)


def candidatos_bfs(grafo, id_usuario):
    """Películas candidatas para un usuario por el recorrido U -> P -> U -> P.

    BFS solo por aristas "vista" hasta el nivel 3:
        nivel 1: películas que vio el usuario
        nivel 2: usuarios que vieron alguna de ellas
        nivel 3: películas de esos usuarios que el usuario no vio (candidatas)
    No atraviesa géneros (no son nodos) ni aristas usuario-usuario.

    Cada candidata incluye cuántos usuarios del nivel 2 la vieron y el camino
    BFS que la explica. Se ordenan por ese conteo (desc.) y luego por id.
    """
    origen = nodo_usuario(id_usuario)
    distancia, padre, _ = bfs(grafo, origen, tipos_arista={ARISTA_VISTA}, max_nivel=3)

    candidatas = []
    for nodo, nivel in distancia.items():
        if nivel != 3:
            continue
        usuarios = sorted(
            grafo.nodos[v]["id"]
            for v in grafo.adyacencia[nodo]
            if distancia.get(v) == 2
        )
        candidatas.append({
            "movie_id": grafo.nodos[nodo]["id"],
            "usuarios": usuarios,
            "camino": reconstruir_camino(padre, nodo),
        })

    candidatas.sort(key=lambda c: (-len(c["usuarios"]), c["movie_id"]))
    return candidatas


# ----------------------------------- DFS -----------------------------------

def dfs(grafo, origen, tipos_arista=None, tipos_nodo=None, visitados=None):
    """Recorrido en profundidad iterativo desde `origen`.

    Devuelve (orden, padre). Los vecinos se apilan en orden inverso para
    visitar en el mismo orden que la versión recursiva.
    """
    if visitados is None:
        visitados = set()
    orden = []
    padre = {}
    pila = [(origen, None)]  # (nodo, desde qué nodo se apiló)

    while pila:
        u, desde = pila.pop()
        if u in visitados:
            continue
        visitados.add(u)
        padre[u] = desde  # el padre es quien lo visitó realmente
        orden.append(u)
        vecinos = list(_vecinos_filtrados(grafo, u, tipos_arista, tipos_nodo))
        for v in reversed(vecinos):
            if v not in visitados:
                pila.append((v, u))

    return orden, padre


def componentes_conexas(grafo, tipos_arista=None, tipos_nodo=None):
    """Componentes conexas con DFS sobre la vista indicada del grafo.

    Devuelve una lista de componentes (cada una, lista ordenada de nodos),
    de mayor a menor tamaño. Son componentes conexas: no implican por sí
    mismas gustos similares.
    """
    visitados = set()
    componentes = []
    for nodo in grafo.adyacencia:
        if tipos_nodo is not None and grafo.nodos[nodo]["tipo"] not in tipos_nodo:
            continue
        if nodo in visitados:
            continue
        orden, _ = dfs(grafo, nodo, tipos_arista, tipos_nodo, visitados)
        componentes.append(sorted(orden))
    componentes.sort(key=lambda c: (-len(c), c[0]))
    return componentes


def componentes_usuarios(grafo):
    """Componentes conexas de la vista de usuarios (aristas usuario-usuario).

    Devuelve {"componentes": [[ids]], "aislados": [ids sin conexiones]}.
    """
    componentes = componentes_conexas(grafo, tipos_arista={ARISTA_USUARIO}, tipos_nodo={TIPO_USUARIO})
    como_ids = [sorted(grafo.nodos[n]["id"] for n in c) for c in componentes]
    return {
        "componentes": como_ids,
        "aislados": sorted(c[0] for c in como_ids if len(c) == 1),
    }


def resumen_componentes(grafo):
    """Cantidad de componentes del grafo completo y de la vista de usuarios.

    En el grafo completo, cada película que nadie vio es una componente de
    un solo nodo (los géneros no son nodos que las unan).
    """
    completas = componentes_conexas(grafo)
    usuarios = componentes_usuarios(grafo)
    peliculas_aisladas = sum(
        1 for c in completas if len(c) == 1 and grafo.nodos[c[0]]["tipo"] == TIPO_PELICULA
    )
    return {
        "grafo_completo": {
            "componentes": len(completas),
            "mayor": len(completas[0]) if completas else 0,
            "peliculas_sin_vistas": peliculas_aisladas,
        },
        "usuarios": {
            "componentes": len(usuarios["componentes"]),
            "mayor": len(usuarios["componentes"][0]) if usuarios["componentes"] else 0,
            "aislados": len(usuarios["aislados"]),
        },
    }
