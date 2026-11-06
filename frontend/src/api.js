async function pedir(url, opciones) {
  const respuesta = await fetch(url, opciones)
  if (!respuesta.ok) throw new Error(`Error ${respuesta.status} en ${url}`)
  return respuesta.json()
}

export const api = {
  usuarios: () => pedir('/api/usuarios'),
  usuario: (id) => pedir(`/api/usuarios/${id}`),
  ver: (idUsuario, idPelicula) => pedir(`/api/usuarios/${idUsuario}/ver/${idPelicula}`, { method: 'POST' }),
  peliculas: ({ genero, q, desde = 0, limite = 40 }) => {
    const params = new URLSearchParams({ desde, limite })
    if (genero) params.set('genero', genero)
    if (q) params.set('q', q)
    return pedir(`/api/peliculas?${params}`)
  },
  grafo: () => pedir('/api/grafo'),
  subGrafo: (id) => pedir(`/api/grafo/${id}`),
  regenerar: (cantidad) => pedir(`/api/generar?cantidad=${cantidad}`, { method: 'POST' }),
}
