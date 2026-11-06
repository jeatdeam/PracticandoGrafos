import { useState } from 'react'

const MIN = 2
const MAX = 300
const ATAJOS = [10, 25, 50, 100]

export default function Setup({ guardados, onGenerar, onContinuar }) {
  const [cantidad, setCantidad] = useState(guardados || 25)
  const [generando, setGenerando] = useState(false)
  const valida = Number.isInteger(cantidad) && cantidad >= MIN && cantidad <= MAX

  const generar = async (e) => {
    e.preventDefault()
    if (!valida) return
    setGenerando(true)
    try {
      await onGenerar(cantidad)
    } finally {
      setGenerando(false)
    }
  }

  return (
    <div className="setup">
      <div className="logo logo-grande">GRAFOFLIX</div>

      <form className="setup-caja" onSubmit={generar}>
        <h1>¿Con cuántos usuarios quieres empezar?</h1>
        <p className="gris">
          Cada usuario se crea con un nombre aleatorio y entre 0 y 100 películas vistas.
          Luego se conectan en un grafo según su género favorito.
        </p>

        <div className="setup-atajos">
          {ATAJOS.map((n) => (
            <button type="button" key={n} className={cantidad === n ? 'activo' : ''} onClick={() => setCantidad(n)}>
              {n}
            </button>
          ))}
        </div>

        <label className="setup-campo">
          <span>Cantidad de usuarios</span>
          <input
            type="number"
            min={MIN}
            max={MAX}
            value={Number.isNaN(cantidad) ? '' : cantidad}
            onChange={(e) => setCantidad(e.target.valueAsNumber)}
          />
        </label>
        {!valida && <p className="generador-error">Ingresa un número entre {MIN} y {MAX}.</p>}

        <button className="boton-rojo" type="submit" disabled={!valida || generando}>
          {generando ? 'Generando...' : `Generar ${valida ? cantidad : ''} usuarios`}
        </button>

        {guardados > 0 && (
          <>
            <div className="setup-separador"><span>o</span></div>
            <button type="button" className="boton-borde" onClick={onContinuar}>
              Continuar con los {guardados} usuarios guardados
            </button>
            <p className="generador-nota">Generar nuevos usuarios reemplaza a los guardados y sus películas vistas.</p>
          </>
        )}
      </form>
    </div>
  )
}
