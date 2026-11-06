import { useEffect, useState } from 'react'
import { api } from '../api'
import { colorGenero } from '../colores'
import MovieCard from './MovieCard'
import MovieModal from './MovieModal'

const POR_PAGINA = 40

export default function Catalog({ perfilId, onVisto }) {
  const [vistas, setVistas] = useState(new Set())
  const [generos, setGeneros] = useState([])
  const [genero, setGenero] = useState('')
  const [texto, setTexto] = useState('')
  const [busqueda, setBusqueda] = useState('')
  const [peliculas, setPeliculas] = useState([])
  const [total, setTotal] = useState(0)
  const [seleccion, setSeleccion] = useState(null)

  useEffect(() => {
    api.usuario(perfilId).then((u) => setVistas(new Set(u.peliculas_vistas.map((p) => p.id))))
  }, [perfilId])

  // Espera a que el usuario deje de escribir antes de buscar
  useEffect(() => {
    const t = setTimeout(() => setBusqueda(texto.trim()), 300)
    return () => clearTimeout(t)
  }, [texto])

  useEffect(() => {
    api.peliculas({ genero, q: busqueda, limite: POR_PAGINA }).then((r) => {
      setPeliculas(r.peliculas)
      setTotal(r.total)
      setGeneros(r.generos)
    })
  }, [genero, busqueda])

  const cargarMas = async () => {
    const r = await api.peliculas({ genero, q: busqueda, desde: peliculas.length, limite: POR_PAGINA })
    setPeliculas((actuales) => [...actuales, ...r.peliculas])
  }

  const ver = async (pelicula) => {
    const resultado = await api.ver(perfilId, pelicula.id)
    setVistas(new Set(resultado.usuario.peliculas_vistas.map((p) => p.id)))
    onVisto(resultado, pelicula)
  }

  return (
    <main className="catalogo">
      <div className="catalogo-cabecera">
        <h1>Explorar películas</h1>
        <input
          className="buscador"
          type="search"
          placeholder="Buscar por título, director o actor"
          value={texto}
          onChange={(e) => setTexto(e.target.value)}
        />
      </div>

      <div className="chips-generos">
        <button className={genero === '' ? 'activo' : ''} onClick={() => setGenero('')}>Todos</button>
        {generos.map((g) => (
          <button
            key={g}
            className={genero === g ? 'activo' : ''}
            style={{ '--chip-color': colorGenero(g) }}
            onClick={() => setGenero(g)}
          >
            {g}
          </button>
        ))}
      </div>

      <p className="gris catalogo-total">{total} películas · {vistas.size} vistas por ti</p>

      {peliculas.length === 0 ? (
        <p className="estado">No hay películas que coincidan con la búsqueda.</p>
      ) : (
        <div className="catalogo-grid">
          {peliculas.map((p) => (
            <MovieCard key={p.id} pelicula={p} vista={vistas.has(p.id)} onClick={setSeleccion} />
          ))}
        </div>
      )}

      {peliculas.length < total && (
        <div className="catalogo-mas">
          <button className="boton-borde" onClick={cargarMas}>Cargar más</button>
        </div>
      )}

      <MovieModal
        pelicula={seleccion}
        vista={seleccion && vistas.has(seleccion.id)}
        onCerrar={() => setSeleccion(null)}
        onVer={ver}
      />
    </main>
  )
}
