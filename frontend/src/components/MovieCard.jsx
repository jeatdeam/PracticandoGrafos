import { colorGenero } from '../colores'

export default function MovieCard({ pelicula, vista, onClick }) {
  const color = colorGenero(pelicula.genero)
  return (
    <button
      className="tarjeta"
      onClick={() => onClick(pelicula)}
      style={{ background: `linear-gradient(160deg, ${color} 0%, #141414 85%)` }}
    >
      <span className="tarjeta-genero">{pelicula.genero}</span>
      {vista && <span className="tarjeta-vista">✓ Vista</span>}
      <span className="tarjeta-titulo">{pelicula.titulo}</span>
      <span className="tarjeta-info">{pelicula.director} · {pelicula.tipo}</span>
    </button>
  )
}
