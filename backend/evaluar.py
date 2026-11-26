"""Validación de las recomendaciones: Precision@N y Recall@N con separación 80/20.

Uso (desde backend/):  python evaluar.py

Procedimiento (sin fuga de información):
    1. Se genera la población con el generador de la app y una semilla fija.
    2. Las vistas de cada usuario se separan al azar (semilla fija): 80 %
       entrenamiento y 20 % prueba (int(0.2 * vistas) películas de prueba).
    3. El grafo se construye SOLO con las vistas de entrenamiento (mismo
       construir_grafo y mismo k). El género favorito y la popularidad
       también se calculan solo con entrenamiento.
    4. Cada recomendador da N películas que el usuario no vio en
       entrenamiento; se comparan con sus películas de prueba:
           Precision@N = aciertos / N
           Recall@N    = aciertos / películas de prueba del usuario
       Se promedian entre los usuarios que tienen al menos una vista de prueba.

Recomendadores comparados (N = 5, igual que las 5 recomendaciones de la app):
    bfs          recomendar_bfs (el de la app)
    aleatorio    N películas al azar no vistas (semilla fija)
    popularidad  las más vistas en entrenamiento
    genero       las primeras N no vistas del género favorito, en el orden del
                 catálogo (lo que hacía la app antes de usar BFS)
    director     recomendar_por_atributo(..., "director"): no vistas del director
                 que más se repite en entrenamiento, por popularidad
    actor        recomendar_por_atributo(..., "actores"): igual con el actor

Las vistas del dataset son sintéticas y aleatorias: el resultado mide qué tan
bien se predicen vistas ocultas, no gustos reales.
"""
import contextlib
import io
import os
import random
import sys
import tempfile
from collections import Counter

from grafo import construir_grafo
from recorridos import recomendar_bfs, recomendar_por_atributo

N = 5
PROPORCION_PRUEBA = 0.2
POBLACIONES = [(25, 7), (25, 42), (100, 7), (100, 42)]
SEMILLA_SEPARACION = 2026
METODOS = ["bfs", "aleatorio", "popularidad", "genero", "director", "actor"]


# ------------------------------- Separación -------------------------------

def separar_vistas(vistas, proporcion=PROPORCION_PRUEBA, semilla=SEMILLA_SEPARACION):
    """Separa las vistas de cada usuario en (entrenamiento, prueba).

    vistas: dict id_usuario -> lista de movie_id. Se baraja una copia de cada
    lista con random.Random(semilla) y las primeras int(proporcion * n) van a
    prueba. Devuelve dos dicts con la misma forma.
    """
    rng = random.Random(semilla)
    entrenamiento, prueba = {}, {}
    for id_usuario in sorted(vistas):
        lista = list(vistas[id_usuario])
        rng.shuffle(lista)
        corte = int(proporcion * len(lista))
        prueba[id_usuario] = lista[:corte]
        entrenamiento[id_usuario] = lista[corte:]
    return entrenamiento, prueba


def genero_favorito(vistas_usuario, genero_de):
    """Género más visto (como Usuario.obtener_generos_vistos); None si no hay vistas."""
    if not vistas_usuario:
        return None
    return Counter(genero_de[m] for m in vistas_usuario).most_common(1)[0][0]


# ----------------------------- Recomendadores -----------------------------

def rec_bfs(grafo, id_usuario, n=N):
    return [r["movie_id"] for r in recomendar_bfs(grafo, id_usuario, n)]


def rec_atributo(grafo, id_usuario, atributo, n=N):
    return [r["movie_id"] for r in recomendar_por_atributo(grafo, id_usuario, atributo, n)["recomendaciones"]]


def rec_aleatorio(vistas_usuario, catalogo, rng, n=N):
    vistas = set(vistas_usuario)
    no_vistas = [m for m in catalogo if m not in vistas]
    return rng.sample(no_vistas, min(n, len(no_vistas)))


def rec_popularidad(vistas_usuario, catalogo, conteo, n=N):
    vistas = set(vistas_usuario)
    candidatas = [m for m in catalogo if m not in vistas]
    candidatas.sort(key=lambda m: (-conteo.get(m, 0), m))
    return candidatas[:n]


def rec_genero(vistas_usuario, catalogo, genero_de, favorito, n=N):
    if favorito is None:
        return []
    vistas = set(vistas_usuario)
    return [m for m in catalogo if genero_de[m] == favorito and m not in vistas][:n]


# --------------------------------- Métricas ---------------------------------

def precision_recall(recomendadas, prueba, n=N):
    """(Precision@n, Recall@n) de un usuario. Precision se divide siempre por n."""
    aciertos = len(set(recomendadas[:n]) & set(prueba))
    return aciertos / n, aciertos / len(prueba), aciertos


def evaluar(peliculas, vistas, n=N, proporcion=PROPORCION_PRUEBA, semilla=SEMILLA_SEPARACION):
    """Evalúa los recomendadores con la misma separación.

    peliculas: lista de dicts con "movie_id" y "genero" (orden del catálogo).
    vistas: dict id_usuario -> lista de movie_id.
    Devuelve {"usuarios_evaluados", "usuarios_sin_prueba", "metodos": {metodo:
    {"precision", "recall", "aciertos"}}, "azar_esperado"}.
    """
    catalogo = [p["movie_id"] for p in peliculas]
    genero_de = {p["movie_id"]: p["genero"] for p in peliculas}
    entrenamiento, prueba = separar_vistas(vistas, proporcion, semilla)

    # Todo lo que usan los recomendadores sale solo de entrenamiento
    usuarios = {
        u: {"nombre": str(u), "genero_favorito": genero_favorito(entrenamiento[u], genero_de), "vistas": entrenamiento[u]}
        for u in entrenamiento
    }
    grafo = construir_grafo(peliculas, usuarios)
    conteo = Counter(m for lista in entrenamiento.values() for m in lista)
    rng = random.Random(semilla)

    sumas = {m: {"precision": 0.0, "recall": 0.0, "aciertos": 0} for m in METODOS}
    evaluados = [u for u in sorted(vistas) if prueba[u]]
    azar = 0.0
    for u in evaluados:
        listas = {
            "bfs": rec_bfs(grafo, u, n),
            "aleatorio": rec_aleatorio(entrenamiento[u], catalogo, rng, n),
            "popularidad": rec_popularidad(entrenamiento[u], catalogo, conteo, n),
            "genero": rec_genero(entrenamiento[u], catalogo, genero_de, usuarios[u]["genero_favorito"], n),
            "director": rec_atributo(grafo, u, "director", n),
            "actor": rec_atributo(grafo, u, "actores", n),
        }
        for metodo, recomendadas in listas.items():
            p, r, a = precision_recall(recomendadas, prueba[u], n)
            sumas[metodo]["precision"] += p
            sumas[metodo]["recall"] += r
            sumas[metodo]["aciertos"] += a
        # Precision@n esperada al azar: películas de prueba / películas no vistas en entrenamiento
        azar += len(prueba[u]) / (len(catalogo) - len(entrenamiento[u]))

    total = len(evaluados)
    return {
        "usuarios_evaluados": total,
        "usuarios_sin_prueba": len(vistas) - total,
        "metodos": {
            m: {
                "precision": s["precision"] / total if total else 0.0,
                "recall": s["recall"] / total if total else 0.0,
                "aciertos": s["aciertos"],
            }
            for m, s in sumas.items()
        },
        "azar_esperado": azar / total if total else 0.0,
    }


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    import servicio  # solo aquí: necesita pandas y faker

    temporal = tempfile.TemporaryDirectory()
    servicio.RUTA_BD = os.path.join(temporal.name, "evaluacion.db")
    proyecto = servicio.Project_Streaming()
    peliculas = list(servicio.peliculas_por_id.values())

    print(f"N = {N}; prueba = {int(PROPORCION_PRUEBA * 100)} % de las vistas de cada usuario; semilla de separación = {SEMILLA_SEPARACION}\n")
    print("| Usuarios | Semilla | Evaluados | Método | Precision@5 | Recall@5 | Aciertos | Precision@5 esperada al azar |")
    print("|---|---|---|---|---|---|---|---|")
    for cantidad, semilla in POBLACIONES:
        with contextlib.redirect_stdout(io.StringIO()):
            proyecto.generar(cantidad, semilla)
        vistas = {u: [p["movie_id"] for p in usuario.get_peliculasVistas()]
                  for u, usuario in proyecto.usuarios_registrados.items()}
        r = evaluar(peliculas, vistas)
        for metodo in METODOS:
            m = r["metodos"][metodo]
            print(f"| {cantidad} | {semilla} | {r['usuarios_evaluados']} | {metodo} | {m['precision']:.4f} | "
                  f"{m['recall']:.4f} | {m['aciertos']} | {r['azar_esperado']:.4f} |")
    temporal.cleanup()


if __name__ == "__main__":
    main()
