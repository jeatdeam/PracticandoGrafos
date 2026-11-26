import { colorGenero } from '../colores'
import { imagenPelicula, ocultarSiFalla } from '../imagenes'

export default function MovieCard({ pelicula, vista, borde = false, vertical = false, onClick }) {
  const color = colorGenero(pelicula.genero)
  return (
    <button
      className={['tarjeta', borde && 'tarjeta-borde', vertical && 'tarjeta-vertical'].filter(Boolean).join(' ')}
      onClick={() => onClick(pelicula)}
      style={{
        background: `linear-gradient(160deg, ${color} 0%, #141414 85%)`,
        // Borde del color del género (fila "Recomendadas para ti")
        ...(borde && { borderColor: color }),
      }}
    >
      <img
        className="portada-imagen"
        src={vertical ? imagenPelicula(pelicula.id, 320, 480) : imagenPelicula(pelicula.id, 440, 248)}
        alt=""
        loading="lazy"
        decoding="async"
        onError={ocultarSiFalla}
      />
      <span
        className="portada-velo"
        style={{ background: `linear-gradient(180deg, ${color}40 0%, rgba(20,20,20,0.1) 35%, rgba(20,20,20,0.92) 100%)` }}
      />
      <span className="tarjeta-genero" style={{ background: color }}>{pelicula.genero}</span>
      {vista && <span className="tarjeta-vista">✓ Vista</span>}
      <span className="tarjeta-titulo">{pelicula.titulo}</span>
      <span className="tarjeta-info">{pelicula.director} · {pelicula.tipo}</span>
    </button>
  )
}
