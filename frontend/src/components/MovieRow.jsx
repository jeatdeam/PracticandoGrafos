import { useRef } from 'react'
import MovieCard from './MovieCard'

export default function MovieRow({ titulo, peliculas, vistas = false, onClick }) {
  const pista = useRef(null)
  const mover = (dir) => pista.current.scrollBy({ left: dir * pista.current.clientWidth * 0.8, behavior: 'smooth' })

  if (!peliculas.length) return null

  return (
    <section className="fila">
      <h2>{titulo} <span className="fila-cantidad">{peliculas.length}</span></h2>
      <div className="fila-contenedor">
        <button className="fila-flecha izq" onClick={() => mover(-1)} aria-label="Anterior">‹</button>
        <div className="fila-pista" ref={pista}>
          {peliculas.map((p) => <MovieCard key={p.id} pelicula={p} vista={vistas} onClick={onClick} />)}
        </div>
        <button className="fila-flecha der" onClick={() => mover(1)} aria-label="Siguiente">›</button>
      </div>
    </section>
  )
}
