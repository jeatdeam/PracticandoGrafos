import { useEffect, useMemo, useState } from 'react'
import { api } from '../api'
import { colorGenero } from '../colores'
import MovieCard from './MovieCard'
import MovieModal from './MovieModal'

const POR_PAGINA = 40

// Mismo filtro que el backend (título, director o actor) para la sección "Ya las viste"
const coincide = (p, genero, busqueda) => {
  if (genero && p.genero !== genero) return false
  if (!busqueda) return true
  const texto = busqueda.toLowerCase()
  return [p.titulo, p.director, p.actores].some((campo) => String(campo).toLowerCase().includes(texto))
}

export default function Catalog({ perfilId, onVisto }) {
  // Historial del usuario, de la más reciente a la más antigua
  const [vistas, setVistas] = useState([])
  const [generos, setGeneros] = useState([])
  const [genero, setGenero] = useState('')
  const [texto, setTexto] = useState('')
  const [busqueda, setBusqueda] = useState('')
  const [peliculas, setPeliculas] = useState([])
  const [total, setTotal] = useState(0)
  const [seleccion, setSeleccion] = useState(null)

  useEffect(() => {
    api.usuario(perfilId).then((u) => setVistas(u.peliculas_vistas))
  }, [perfilId])

  // Espera a que el usuario deje de escribir antes de buscar
  useEffect(() => {
    const t = setTimeout(() => setBusqueda(texto.trim()), 300)
    return () => clearTimeout(t)
  }, [texto])

  // El backend ya quita las que vio este usuario
  useEffect(() => {
    api.peliculas({ genero, q: busqueda, limite: POR_PAGINA, sinVistasDe: perfilId }).then((r) => {
      setPeliculas(r.peliculas)
      setTotal(r.total)
      setGeneros(r.generos)
    })
  }, [genero, busqueda, perfilId])

  const cargarMas = async () => {
    const r = await api.peliculas({ genero, q: busqueda, desde: peliculas.length, limite: POR_PAGINA, sinVistasDe: perfilId })
    setPeliculas((actuales) => [...actuales, ...r.peliculas.filter((p) => !actuales.some((a) => a.id === p.id))])
  }

  const idsVistas = useMemo(() => new Set(vistas.map((p) => p.id)), [vistas])
  const vistasFiltradas = useMemo(() => vistas.filter((p) => coincide(p, genero, busqueda)), [vistas, genero, busqueda])

  const ver = async (pelicula) => {
    const resultado = await api.ver(perfilId, pelicula.id)
    // Queda en su historial: sale de Explorar y pasa a "Ya las viste"
    setVistas(resultado.usuario.peliculas_vistas)
    if (resultado.nueva) {
      setPeliculas((actuales) => actuales.filter((p) => p.id !== pelicula.id))
      setTotal((t) => Math.max(0, t - 1))
    }
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

      <p className="gris catalogo-total">{total} películas por ver · {vistas.length} vistas por ti</p>

      {peliculas.length === 0 ? (
        <p className="estado">No hay películas por ver que coincidan con la búsqueda.</p>
      ) : (
        <div className="catalogo-grid">
          {peliculas.map((p) => (
            <MovieCard key={p.id} pelicula={p} vista={false} onClick={setSeleccion} />
          ))}
        </div>
      )}

      {peliculas.length < total && (
        <div className="catalogo-mas">
          <button className="boton-borde" onClick={cargarMas}>Cargar más</button>
        </div>
      )}

      {vistasFiltradas.length > 0 && (
        <section className="catalogo-vistas">
          <h2>Ya las viste <span className="fila-cantidad">{vistasFiltradas.length}</span></h2>
          <div className="catalogo-grid">
            {vistasFiltradas.map((p) => (
              <MovieCard key={p.id} pelicula={p} vista onClick={setSeleccion} />
            ))}
          </div>
        </section>
      )}

      <MovieModal
        pelicula={seleccion}
        vista={seleccion && idsVistas.has(seleccion.id)}
        onCerrar={() => setSeleccion(null)}
        onVer={ver}
      />
    </main>
  )
}
