import { useEffect, useMemo, useState } from 'react'
import { api } from '../api'
import { colorGenero } from '../colores'
import MovieCard from './MovieCard'
import MovieModal from './MovieModal'
import CargandoEsfera from './CargandoEsfera'

// Todas las películas que vio el usuario, agrupadas por género
// (del género que más vio al que menos; dentro, de la más reciente a la más antigua)
export default function Historial({ perfilId, onVolver }) {
  const [detalle, setDetalle] = useState(null)
  const [seleccion, setSeleccion] = useState(null)

  useEffect(() => {
    api.usuario(perfilId).then(setDetalle)
    window.scrollTo(0, 0)
  }, [perfilId])

  const porGenero = useMemo(() => {
    if (!detalle) return []
    return Object.entries(detalle.generos).map(([g, n]) => [g, n, detalle.peliculas_vistas.filter((p) => p.genero === g)])
  }, [detalle])

  if (!detalle) return <div className="estado"><CargandoEsfera tamano={140} texto="Cargando historial..." /></div>

  return (
    <main className="catalogo historial">
      <div className="catalogo-cabecera">
        <div>
          <button className="historial-volver" onClick={onVolver}>‹ Volver al perfil</button>
          <h1>Películas vistas por {detalle.nombre} {detalle.apellido}</h1>
        </div>
      </div>

      <p className="gris catalogo-total">
        {detalle.cantidad_vistas} películas en {porGenero.length} {porGenero.length === 1 ? 'género' : 'géneros'}
        {detalle.genero_favorito && <> · favorito: <strong style={{ color: colorGenero(detalle.genero_favorito) }}>{detalle.genero_favorito}</strong></>}
      </p>

      {porGenero.length > 0 && (
        <nav className="chips-generos">
          {porGenero.map(([g, n]) => (
            <a key={g} href={`#historial-${g}`} style={{ '--chip-color': colorGenero(g) }}>{g} · {n}</a>
          ))}
        </nav>
      )}

      {porGenero.length === 0 ? (
        <p className="estado">Todavía no ha visto ninguna película.</p>
      ) : (
        porGenero.map(([g, n, lista]) => (
          <section key={g} id={`historial-${g}`} className="historial-genero">
            <h2 style={{ borderColor: colorGenero(g) }}>
              {g} <span className="fila-cantidad">{n}</span>
            </h2>
            <div className="catalogo-grid">
              {lista.map((p) => <MovieCard key={p.id} pelicula={p} vista onClick={setSeleccion} />)}
            </div>
          </section>
        ))
      )}

      <MovieModal pelicula={seleccion} vista onCerrar={() => setSeleccion(null)} onVer={() => {}} />
    </main>
  )
}
