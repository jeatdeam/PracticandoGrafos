"""Kruskal con UFDS, como en MST_Algoritmo_Kruskal.ipynb, aplicado a la vista de usuarios.

La clase Graph es la del notebook: lista de aristas [u, v, w], find recursivo
(sin compresión de caminos) y applyUnion con unión por rango (parent, rank).
Dos adaptaciones aprobadas por el equipo:
    1. El while también se detiene al agotar la lista de aristas ordenadas
       (i < len(self.graph)): si el grafo es disconexo, el resultado es un
       bosque de expansión mínima, uno por componente, sin IndexError.
    2. kruskalMST devuelve (result, tot_weight) en vez de imprimirlos.

Uso en GrafoFlix: "red simplificada" de la vista de usuarios. El peso de una
arista usuario-usuario es la distancia de Jaccard entre las películas vistas
(1 - comunes / unión): cuanto más se parecen, menor costo. El bosque conserva
las conexiones de mayor similitud con U - c aristas (c = número de árboles,
que debe coincidir con las componentes conexas que da DFS).
"""
from grafo import ARISTA_USUARIO, ARISTA_VISTA
from recorridos import nodos_usuario


class Graph:
    def __init__(self, vertices):
        self.V = vertices
        self.graph = []

    def addEdge(self, u, v, w):
        self.graph.append([u, v, w])

    # Función de búsqueda Union-Find
    def find(self, parent, i):
        if parent[i] == i:
            return i
        return self.find(parent, parent[i])

    def applyUnion(self, parent, rank, x, y):
        xroot = self.find(parent, x)
        yroot = self.find(parent, y)
        if rank[xroot] < rank[yroot]:
            parent[xroot] = yroot
        elif rank[xroot] > rank[yroot]:
            parent[yroot] = xroot
        else:
            parent[yroot] = xroot
            rank[xroot] += 1

    # Aplicando el Algoritmo de Kruskal
    def kruskalMST(self):
        result = []
        i, e, tot_weight = 0, 0, 0
        self.graph = sorted(self.graph, key=lambda item: item[2])
        parent = []
        rank = []
        for node in range(self.V):
            parent.append(node)
            rank.append(0)

        # Adaptación 1: i < len(self.graph) (lista de aristas ya ordenada) -> bosque si es disconexo
        while e < self.V - 1 and i < len(self.graph):
            u, v, w = self.graph[i]
            i = i + 1
            x = self.find(parent, u)
            y = self.find(parent, v)
            if x != y:
                e = e + 1
                result.append([u, v, w])
                self.applyUnion(parent, rank, x, y)

        for u, v, weight in result:
            tot_weight += weight

        # Adaptación 2: devolver en vez de imprimir
        return result, tot_weight


def distancia_jaccard(a, b):
    """1 - |a ∩ b| / |a ∪ b| para dos conjuntos de películas vistas (0 = vieron lo mismo)."""
    union = a | b
    if not union:
        return 1.0
    return 1 - len(a & b) / len(union)


def bosque_expansion_minima(grafo):
    """Kruskal sobre la vista de usuarios con peso = distancia de Jaccard.

    Cada arista usuario-usuario del grafo único se agrega una sola vez
    (grafo.aristas guarda cada par no dirigido una vez). Los usuarios se
    numeran 0..U-1 en orden de id, como los vértices del notebook.

    Devuelve {"aristas": [{source, target, peso}], "costo_total",
    "arboles", "aristas_grafo"}. arboles = U - aristas del bosque (cuenta
    también a los usuarios aislados).
    Tiempo: ordenar O(E log E) + E llamadas a find de O(log V) (unión por
    rango, sin compresión) = O(E log E). Espacio: O(V + E).
    """
    nodos = nodos_usuario(grafo)
    usuarios = [grafo.nodos[n]["id"] for n in nodos]
    indice = {id_usuario: i for i, id_usuario in enumerate(usuarios)}
    # Películas vistas de cada usuario, calculadas una sola vez (no una vez por arista)
    vistas = {n: set(grafo.vecinos(n, ARISTA_VISTA)) for n in nodos}

    g = Graph(len(usuarios))
    for (a, b), atributos in grafo.aristas.items():
        if atributos["tipo"] == ARISTA_USUARIO:
            g.addEdge(indice[grafo.nodos[a]["id"]], indice[grafo.nodos[b]["id"]], distancia_jaccard(vistas[a], vistas[b]))

    result, tot_weight = g.kruskalMST()
    return {
        "aristas": [{"source": usuarios[u], "target": usuarios[v], "peso": w} for u, v, w in result],
        "costo_total": tot_weight,
        "arboles": len(usuarios) - len(result),
        "aristas_grafo": len(g.graph),
    }
