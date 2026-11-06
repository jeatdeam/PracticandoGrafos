import { useEffect, useState } from 'react'
import { colorGenero } from '../colores'

export default function MovieModal({ pelicula, vista, onCerrar, onVer }) {
  const [cargando, setCargando] = useState(false)

  useEffect(() => {
    const alTeclado = (e) => e.key === 'Escape' && onCerrar()
    window.addEventListener('keydown', alTeclado)
    return () => window.removeEventListener('keydown', alTeclado)
  }, [onCerrar])

  if (!pelicula) return null

  const ver = async () => {
    setCargando(true)
    try {
      await onVer(pelicula)
    } finally {
      setCargando(false)
    }
  }

  return (
    <div className="modal-fondo" onClick={onCerrar}>
      <div className="modal" onClick={(e) => e.stopPropagation()}>
        <div className="modal-portada" style={{ background: `linear-gradient(160deg, ${colorGenero(pelicula.genero)}, #181818 90%)` }}>
          <button className="modal-cerrar" onClick={onCerrar} aria-label="Cerrar">✕</button>
          <h2>{pelicula.titulo}</h2>
          {vista ? (
            <span className="modal-visto">✓ Ya la viste</span>
          ) : (
            <button className="boton-blanco" onClick={ver} disabled={cargando}>
              {cargando ? 'Guardando...' : '▶ Ver'}
            </button>
          )}
        </div>
        <div className="modal-cuerpo">
          <p className="modal-meta">
            <span className="chip">{pelicula.genero}</span>
            <span className="chip">{pelicula.tipo}</span>
          </p>
          <p><strong>Director:</strong> {pelicula.director}</p>
          <p><strong>Reparto:</strong> {pelicula.actores}</p>
          <p><strong>Presupuesto:</strong> ${pelicula.presupuesto} M</p>
          <p className="gris">ID: {pelicula.id}</p>
        </div>
      </div>
    </div>
  )
}
