"""Mide cómo cambia la vista de usuarios según el umbral k de películas en común.

Uso (desde backend/):  python medir_grafo.py

Para cada población (cantidad de usuarios, semilla) genera los usuarios con el
mismo generador de la app y construye el grafo con k = 1..5 (el criterio por
género favorito no depende de k). Usa una base SQLite temporal: no toca
streaming.db. Con la misma semilla el resultado es siempre el mismo.
"""
import contextlib
import io
import os
import sys
import tempfile

import servicio
from grafo import ARISTA_USUARIO, MOTIVO_GENERO, MOTIVO_PELICULAS, construir_grafo
from recorridos import componentes_usuarios

POBLACIONES = [(25, 7), (25, 42), (100, 7), (100, 42)]
VALORES_K = [1, 2, 3, 4, 5]


def datos_usuarios(proyecto):
    return {
        id_usuario: {
            "nombre": u.nombre,
            "genero_favorito": u.get_generoFav(),
            "vistas": [p["movie_id"] for p in u.get_peliculasVistas()],
        }
        for id_usuario, u in proyecto.usuarios_registrados.items()
    }


def medir(usuarios, k):
    grafo = construir_grafo(servicio.peliculas_por_id.values(), usuarios, min_comunes=k)
    n = len(usuarios)
    aristas = [a for a in grafo.aristas.values() if a["tipo"] == ARISTA_USUARIO]
    solo_genero = sum(1 for a in aristas if a["motivos"] == [MOTIVO_GENERO])
    solo_peliculas = sum(1 for a in aristas if a["motivos"] == [MOTIVO_PELICULAS])
    ambos = len(aristas) - solo_genero - solo_peliculas
    comp = componentes_usuarios(grafo)
    return {
        "aristas": len(aristas),
        "densidad": len(aristas) / (n * (n - 1) / 2),
        "solo_genero": solo_genero,
        "solo_peliculas": solo_peliculas,
        "ambos": ambos,
        "componentes": len(comp["componentes"]),
        "mayor": len(comp["componentes"][0]),
        "aislados": len(comp["aislados"]),
    }


def main():
    sys.stdout.reconfigure(encoding="utf-8")  # tildes correctas también en la consola de Windows
    temporal = tempfile.TemporaryDirectory()
    servicio.RUTA_BD = os.path.join(temporal.name, "medicion.db")
    proyecto = servicio.Project_Streaming()

    print("| Usuarios | Semilla | k | Aristas U-U | Densidad | Solo género | Solo películas | Ambos | Componentes | Mayor | Aislados |")
    print("|---|---|---|---|---|---|---|---|---|---|---|")
    for cantidad, semilla in POBLACIONES:
        with contextlib.redirect_stdout(io.StringIO()):  # silencia avisos del generador
            proyecto.generar(cantidad, semilla)
        usuarios = datos_usuarios(proyecto)
        for k in VALORES_K:
            m = medir(usuarios, k)
            print(f"| {cantidad} | {semilla} | {k} | {m['aristas']} | {m['densidad']:.2f} | {m['solo_genero']} | "
                  f"{m['solo_peliculas']} | {m['ambos']} | {m['componentes']} | {m['mayor']} | {m['aislados']} |")
    temporal.cleanup()


if __name__ == "__main__":
    main()
