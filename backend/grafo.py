"""Grafo único de GrafoFlix: usuarios y películas en una lista de adyacencia.

Nodos:
    U:<id_usuario>   un perfil
    P:<movie_id>     una película del catálogo (CSV)

Aristas (no dirigidas):
    vista    usuario - película   el usuario vio la película
    usuario  usuario - usuario    mismo género favorito válido O películas en común

Los géneros son atributos de los nodos, no nodos. Como hay aristas
usuario-usuario, el grafo no es estrictamente bipartito.

Este módulo no depende de pandas ni de FastAPI para poder probarse solo.
"""

PREFIJO_USUARIO = "U:"
PREFIJO_PELICULA = "P:"

TIPO_USUARIO = "usuario"
TIPO_PELICULA = "pelicula"

ARISTA_VISTA = "vista"
ARISTA_USUARIO = "usuario"

MOTIVO_GENERO = "genero"
MOTIVO_PELICULAS = "peliculas"

# Provisional: lectura literal de "tienen películas vistas en común".
# Se revisará al medir la densidad del grafo (pendiente de decisión).
MIN_PELICULAS_COMUNES = 1


def nodo_usuario(id_usuario):
    return f"{PREFIJO_USUARIO}{id_usuario}"


def nodo_pelicula(movie_id):
    return f"{PREFIJO_PELICULA}{movie_id}"


def clave_arista(a, b):
    """La misma clave para (a, b) y (b, a): el grafo es no dirigido."""
    return (a, b) if a <= b else (b, a)


class Grafo:

    def __init__(self):
        self.adyacencia = {}  # nodo -> lista de nodos vecinos
        self.nodos = {}       # nodo -> atributos (tipo, género, ...)
        self.aristas = {}     # clave_arista -> atributos (tipo, motivos, comunes)

    def agregar_nodo(self, nodo, **atributos):
        if nodo not in self.adyacencia:
            self.adyacencia[nodo] = []
        self.nodos[nodo] = atributos

    def agregar_arista(self, a, b, **atributos):
        if a == b:
            raise ValueError("No se permiten lazos (arista de un nodo consigo mismo)")
        if a not in self.adyacencia or b not in self.adyacencia:
            raise KeyError(f"Ambos nodos deben existir antes de unirlos: {a}, {b}")
        clave = clave_arista(a, b)
        if clave in self.aristas:
            return  # ya existe: no se duplica en la lista de adyacencia
        self.aristas[clave] = atributos
        self.adyacencia[a].append(b)
        self.adyacencia[b].append(a)

    def arista(self, a, b):
        return self.aristas.get(clave_arista(a, b))

    def vecinos(self, nodo, tipo_arista=None):
        if tipo_arista is None:
            return list(self.adyacencia[nodo])
        return [v for v in self.adyacencia[nodo] if self.aristas[clave_arista(nodo, v)]["tipo"] == tipo_arista]

    def usuarios_conectados(self, id_usuario):
        """Ids de los usuarios unidos a este por una arista usuario-usuario."""
        return [
            self.nodos[v]["id"]
            for v in self.vecinos(nodo_usuario(id_usuario), ARISTA_USUARIO)
        ]

    def conteo(self):
        vertices = {TIPO_USUARIO: 0, TIPO_PELICULA: 0}
        for atributos in self.nodos.values():
            vertices[atributos["tipo"]] += 1
        aristas = {ARISTA_VISTA: 0, ARISTA_USUARIO: 0}
        for atributos in self.aristas.values():
            aristas[atributos["tipo"]] += 1
        return {
            "vertices": {**vertices, "total": len(self.nodos)},
            "aristas": {**aristas, "total": len(self.aristas)},
        }


def motivos_conexion(genero_1, genero_2, comunes, min_comunes=MIN_PELICULAS_COMUNES):
    """Motivos por los que dos usuarios quedan conectados (lista vacía = sin arista).

    Un género favorito None (usuario sin vistas) nunca coincide con otro.
    """
    motivos = []
    if genero_1 is not None and genero_1 == genero_2:
        motivos.append(MOTIVO_GENERO)
    if len(comunes) >= min_comunes:
        motivos.append(MOTIVO_PELICULAS)
    return motivos


def construir_grafo(peliculas, usuarios, min_comunes=MIN_PELICULAS_COMUNES):
    """Construye el grafo completo.

    peliculas: iterable de dicts con al menos "movie_id" y "genero".
    usuarios:  dict id_usuario -> {"nombre", "genero_favorito", "vistas": iterable de movie_id}

    Coste: O(P + suma de vistas) para nodos y aristas "vista", y
    O(U^2 * m) para comparar todos los pares de usuarios (m = vistas promedio).
    """
    if min_comunes < 1:
        raise ValueError("min_comunes debe ser al menos 1")

    grafo = Grafo()

    for p in peliculas:
        grafo.agregar_nodo(
            nodo_pelicula(p["movie_id"]),
            tipo=TIPO_PELICULA,
            id=p["movie_id"],
            titulo=p.get("titulo"),
            genero=p["genero"],
        )

    vistas = {}
    for id_usuario, datos in usuarios.items():
        grafo.agregar_nodo(
            nodo_usuario(id_usuario),
            tipo=TIPO_USUARIO,
            id=id_usuario,
            nombre=datos.get("nombre"),
            genero=datos.get("genero_favorito"),
        )
        # Solo películas que existen como nodo del grafo
        vistas[id_usuario] = {m for m in datos["vistas"] if nodo_pelicula(m) in grafo.nodos}

    for id_usuario, conjunto in vistas.items():
        for movie_id in sorted(conjunto):
            grafo.agregar_arista(nodo_usuario(id_usuario), nodo_pelicula(movie_id), tipo=ARISTA_VISTA)

    ids = list(usuarios)
    for i in range(len(ids)):
        for j in range(i + 1, len(ids)):
            u, v = ids[i], ids[j]
            comunes = sorted(vistas[u] & vistas[v])
            motivos = motivos_conexion(
                usuarios[u].get("genero_favorito"),
                usuarios[v].get("genero_favorito"),
                comunes,
                min_comunes,
            )
            if motivos:
                grafo.agregar_arista(
                    nodo_usuario(u), nodo_usuario(v),
                    tipo=ARISTA_USUARIO, motivos=motivos, comunes=comunes,
                )

    return grafo
