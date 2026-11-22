"""Recorridos BFS y DFS sobre el grafo único (grafo.py).

Siguen las implementaciones vistas en clase, adaptadas a nuestra lista de
adyacencia (diccionario nodo -> vecinos) y a ids de nodo "U:<id>" / "P:<id>":

    BFS (como bfs_am de BFS_MA.ipynb): lista `queue` usada como cola con
        pop(0), `visited` y `path` (padres). Agrega `nivel` para saber a qué
        distancia está cada nodo.
    DFS (como dfs de DFS_LA.ipynb): función interna recursiva `_dfs`,
        `visited` y `path`.

Hay una sola implementación de cada uno; los usos se distinguen por el tipo
de arista que se recorre:
    - animación de /api/recorrido: BFS o DFS por aristas usuario-usuario
    - recomendaciones (recomendar_bfs): BFS por aristas "vista" hasta el nivel 3
    - componentes conexas: DFS por aristas usuario-usuario
"""
from grafo import ARISTA_USUARIO, ARISTA_VISTA, TIPO_PELICULA, TIPO_USUARIO, nodo_pelicula, nodo_usuario


def vecinos(grafo, u, tipo_arista=None):
    """Vecinos de u (solo por aristas del tipo indicado), ordenados por id."""
    return sorted(
        grafo.vecinos(u, tipo_arista),
        key=lambda v: (grafo.nodos[v]["tipo"], grafo.nodos[v]["id"]),
    )


def nuevos_visitados(grafo):
    """Como `visited = [False]*n` del notebook, pero por nodo."""
    return {nodo: False for nodo in grafo.adyacencia}


# ----------------------------------- BFS -----------------------------------

def bfs(grafo, s, tipo_arista=None, max_nivel=None, visited=None, pasos=None, componente=1):
    """Búsqueda en amplitud desde s.

    Devuelve (path, nivel):
        path[n]   nodo desde el que se descubrió n (s -> None)
        nivel[n]  número de aristas desde s hasta n
    max_nivel: no se expanden los nodos de ese nivel (se descubren, pero no
        se sigue desde ellos).
    visited: se puede pasar para continuar con otra componente.
    pasos: si es una lista, se agrega un paso por cada nodo que sale de la
        cola, con el estado de la cola en ese momento (para la animación).

    Tiempo: O(V + E) visitas; cada pop(0) cuesta O(largo de la cola), así que
    en el peor caso O(V^2 + E). Espacio: O(V).
    """
    if visited is None:
        visited = nuevos_visitados(grafo)
    path = {s: None}
    nivel = {s: 0}
    queue = [s]
    visited[s] = True

    while queue:
        u = queue.pop(0)
        if max_nivel is None or nivel[u] < max_nivel:
            for v in vecinos(grafo, u, tipo_arista):
                if not visited[v]:
                    visited[v] = True
                    path[v] = u
                    nivel[v] = nivel[u] + 1
                    queue.append(v)
        if pasos is not None:
            pasos.append({"nodo": u, "padre": path[u], "componente": componente, "estructura": list(queue)})

    return path, nivel


def reconstruir_camino(path, destino):
    """Camino desde el origen hasta destino siguiendo los padres; [] si no se alcanzó."""
    if destino not in path:
        return []
    camino = []
    nodo = destino
    while nodo is not None:
        camino.append(nodo)
        nodo = path[nodo]
    camino.reverse()
    return camino


def camino_entre_usuarios(grafo, id_origen, id_destino):
    """Camino mínimo en saltos entre dos usuarios (BFS por aristas usuario-usuario)."""
    path, _ = bfs(grafo, nodo_usuario(id_origen), ARISTA_USUARIO)
    return reconstruir_camino(path, nodo_usuario(id_destino))


def candidatos_bfs(grafo, id_usuario):
    """Películas candidatas para un usuario por el recorrido U -> P -> U -> P.

    BFS solo por aristas "vista" hasta el nivel 3:
        nivel 1: películas que vio el usuario
        nivel 2: usuarios que vieron alguna de ellas
        nivel 3: películas de esos usuarios que el usuario no vio (candidatas)
    No pasa por aristas usuario-usuario ni por géneros (no son nodos).

    Cada candidata incluye los usuarios del nivel 2 que la vieron y el camino
    BFS que la explica. Se ordenan por cantidad de esos usuarios y luego por id.
    """
    path, nivel = bfs(grafo, nodo_usuario(id_usuario), ARISTA_VISTA, max_nivel=3)

    candidatas = []
    for nodo in path:
        if nivel[nodo] != 3:
            continue
        usuarios = sorted(
            grafo.nodos[v]["id"]
            for v in grafo.adyacencia[nodo]
            if nivel.get(v) == 2
        )
        candidatas.append({
            "movie_id": grafo.nodos[nodo]["id"],
            "usuarios": usuarios,
            "camino": reconstruir_camino(path, nodo),
        })

    candidatas.sort(key=lambda c: (-len(c["usuarios"]), c["movie_id"]))
    return candidatas


def recomendar_bfs(grafo, id_usuario, n=5):
    """Las n mejores recomendaciones para un usuario a partir del BFS.

    Puntaje de una candidata = suma, sobre los usuarios del nivel 2 que la
    vieron, de cuántas películas tienen en común con el usuario (un vecino
    más parecido en lo que vio pesa más). Desempate: primero las del género
    favorito del usuario (el género solo ordena) y luego por id.

    Si el BFS da menos de n candidatas (por ejemplo, un usuario sin vistas),
    se completa con las películas más vistas que el usuario no vio, marcadas
    con origen "popularidad".

    Cada recomendación: {movie_id, origen, puntaje, usuarios, camino}.
    Tiempo: el del BFS, más O(L * m) para contar películas en común con los
    L usuarios del nivel 2 (m = vistas por usuario), más ordenar las C
    candidatas O(C log C).
    """
    u = nodo_usuario(id_usuario)
    vistas_u = set(grafo.vecinos(u, ARISTA_VISTA))
    genero_u = grafo.nodos[u]["genero"]

    comunes = {}  # usuario del nivel 2 -> películas en común con u
    recomendaciones = []
    for c in candidatos_bfs(grafo, id_usuario):
        puntaje = 0
        for id_v in c["usuarios"]:
            v = nodo_usuario(id_v)
            if v not in comunes:
                comunes[v] = len(vistas_u & set(grafo.vecinos(v, ARISTA_VISTA)))
            puntaje += comunes[v]
        recomendaciones.append({
            "movie_id": c["movie_id"],
            "origen": "bfs",
            "puntaje": puntaje,
            "usuarios": c["usuarios"],
            "camino": c["camino"],
        })

    def es_otro_genero(r):
        return grafo.nodos[nodo_pelicula(r["movie_id"])]["genero"] != genero_u

    recomendaciones.sort(key=lambda r: (-r["puntaje"], es_otro_genero(r), r["movie_id"]))
    recomendaciones = recomendaciones[:n]

    if len(recomendaciones) < n:
        # Respaldo: películas más vistas (más aristas "vista") que no vio ni ya se eligieron
        elegidas = {nodo_pelicula(r["movie_id"]) for r in recomendaciones}
        populares = [
            p for p, atributos in grafo.nodos.items()
            if atributos["tipo"] == TIPO_PELICULA and p not in vistas_u and p not in elegidas
        ]
        populares.sort(key=lambda p: (-len(grafo.adyacencia[p]), grafo.nodos[p]["id"]))
        for p in populares[: n - len(recomendaciones)]:
            recomendaciones.append({
                "movie_id": grafo.nodos[p]["id"],
                "origen": "popularidad",
                "puntaje": len(grafo.adyacencia[p]),
                "usuarios": [],
                "camino": [],
            })

    return recomendaciones


# ----------------------------------- DFS -----------------------------------

def dfs(grafo, s, tipo_arista=None, visited=None, pasos=None, componente=1):
    """Búsqueda en profundidad recursiva desde s (como en DFS_LA.ipynb).

    Devuelve path: path[n] es el nodo desde el que se visitó n (s -> None).
    Las claves de path quedan en el orden de visita.
    pasos: si es una lista, se agrega un paso por cada nodo visitado, con la
        pila de llamadas recursivas activas en ese momento (para la animación;
        no cambia el algoritmo).

    Se usa sobre la vista de usuarios: la profundidad de la recursión es como
    máximo la cantidad de usuarios (<= 300), dentro del límite de Python.
    Tiempo: O(V + E). Espacio: O(V) por la pila de recursión.
    """
    if visited is None:
        visited = nuevos_visitados(grafo)
    path = {s: None}
    llamadas = []  # nodos cuyas llamadas a _dfs siguen abiertas

    def _dfs(u):
        visited[u] = True
        llamadas.append(u)
        if pasos is not None:
            pasos.append({"nodo": u, "padre": path[u], "componente": componente, "estructura": list(llamadas)})
        for v in vecinos(grafo, u, tipo_arista):
            if not visited[v]:
                path[v] = u
                _dfs(v)
        llamadas.pop()

    _dfs(s)
    return path


def nodos_usuario(grafo):
    """Nodos de usuario ordenados por id."""
    return sorted(
        (n for n, atributos in grafo.nodos.items() if atributos["tipo"] == TIPO_USUARIO),
        key=lambda n: grafo.nodos[n]["id"],
    )


def componentes_usuarios(grafo):
    """Componentes conexas de la vista de usuarios, con DFS por aristas usuario-usuario.

    Devuelve {"componentes": [[ids]], "aislados": [ids sin conexiones]}, con
    las componentes de mayor a menor tamaño. Son componentes conexas: no
    implican por sí mismas gustos similares.
    """
    visited = nuevos_visitados(grafo)
    componentes = []
    for s in nodos_usuario(grafo):
        if not visited[s]:
            path = dfs(grafo, s, ARISTA_USUARIO, visited)
            componentes.append(sorted(grafo.nodos[n]["id"] for n in path))
    componentes.sort(key=lambda c: (-len(c), c[0]))
    return {
        "componentes": componentes,
        "aislados": sorted(c[0] for c in componentes if len(c) == 1),
    }


def resumen_componentes(grafo):
    """Componentes de la vista de usuarios y películas que nadie vio."""
    usuarios = componentes_usuarios(grafo)
    peliculas_sin_vistas = sum(
        1 for n, atributos in grafo.nodos.items()
        if atributos["tipo"] == TIPO_PELICULA and not grafo.adyacencia[n]
    )
    return {
        "componentes": len(usuarios["componentes"]),
        "mayor": len(usuarios["componentes"][0]) if usuarios["componentes"] else 0,
        "aislados": len(usuarios["aislados"]),
        "peliculas_sin_vistas": peliculas_sin_vistas,
    }


# ------------------------- Animación de /api/recorrido -------------------------

def recorrido_pasos(grafo, tipo, id_inicio, todo=False):
    """Pasos de un BFS o DFS por la vista de usuarios, para animarlos.

    Empieza en id_inicio y recorre su componente. Con todo=True, al terminar
    sigue desde el siguiente usuario sin visitar hasta cubrir todas las
    componentes. Cada paso: {nodo, padre, componente, estructura}, con ids de
    usuario; estructura es la cola (BFS) o la pila de llamadas (DFS).
    """
    if tipo not in ("bfs", "dfs"):
        raise ValueError("El recorrido debe ser bfs o dfs")
    inicio = nodo_usuario(id_inicio)
    orden_inicio = [inicio] + ([n for n in nodos_usuario(grafo) if n != inicio] if todo else [])

    visited = nuevos_visitados(grafo)
    pasos = []
    componente = 0
    for s in orden_inicio:
        if visited[s]:
            continue
        componente += 1
        if tipo == "bfs":
            bfs(grafo, s, ARISTA_USUARIO, visited=visited, pasos=pasos, componente=componente)
        else:
            dfs(grafo, s, ARISTA_USUARIO, visited=visited, pasos=pasos, componente=componente)

    def id_de(n):
        return None if n is None else grafo.nodos[n]["id"]

    pasos = [
        {**p, "nodo": id_de(p["nodo"]), "padre": id_de(p["padre"]), "estructura": [id_de(n) for n in p["estructura"]]}
        for p in pasos
    ]
    return {
        "tipo": tipo,
        "inicio": id_inicio,
        "componentes": componente,
        "miembros": sorted(p["nodo"] for p in pasos),
        "pasos": pasos,
    }
