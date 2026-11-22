import { useEffect, useRef, useState } from 'react'
import { sonarFin, sonarVisita } from '../sonido'
import CargandoEsfera from './CargandoEsfera'

const VELOCIDADES = [
  { etiqueta: 'Lenta', ms: 1100 },
  { etiqueta: 'Normal', ms: 550 },
  { etiqueta: 'Rápida', ms: 180 },
]

const EXPLICACION = {
  bfs: 'BFS (búsqueda en anchura) usa una cola: saca al primer usuario de la cola, mete al final a todos sus vecinos sin visitar y repite. Avanza por niveles desde el inicio.',
  dfs: 'DFS (búsqueda en profundidad) usa una pila: desde el usuario del tope baja al primer vecino sin visitar; cuando ya no quedan, lo saca de la pila (retrocede) y prueba otro camino.',
}

/** Controles y estado paso a paso de un recorrido BFS/DFS. */
export default function RecorridoPanel({ tipo, datos, paso, setPaso, nombreDe, grafoListo = true }) {
  const [reproduciendo, setReproduciendo] = useState(false)
  const [velocidad, setVelocidad] = useState(1)
  const total = datos?.pasos.length ?? 0
  // Sonido activado o no (se recuerda en este navegador)
  const [sonido, setSonido] = useState(() => {
    try { return localStorage.getItem('sonidoRecorrido') !== 'no' } catch { return true }
  })
  const pasoAnterior = useRef(paso)

  const cambiarSonido = () => {
    setSonido(!sonido)
    try { localStorage.setItem('sonidoRecorrido', sonido ? 'no' : 'si') } catch { /* sin almacenamiento */ }
  }

  // Suena al avanzar de a un nodo (reproduciendo o con "paso siguiente");
  // saltos grandes (reiniciar, ir al final) o retroceder no suenan
  useEffect(() => {
    const antes = pasoAnterior.current
    pasoAnterior.current = paso
    if (!sonido || !datos || paso !== antes + 1) return
    const visita = datos.pasos[paso - 1]
    sonarVisita(tipo, paso - 1, visita.padre === null)
    if (paso === total) setTimeout(sonarFin, 350)
  }, [paso])

  // Al cargar un recorrido nuevo arranca solo, pero solo cuando el grafo ya
  // está dibujado; mientras se dibuja queda en pausa en el paso 0
  useEffect(() => setReproduciendo(total > 0 && grafoListo), [datos, grafoListo])

  useEffect(() => {
    if (!reproduciendo) return
    if (paso >= total) {
      setReproduciendo(false)
      return
    }
    const id = setTimeout(() => setPaso(paso + 1), VELOCIDADES[velocidad].ms)
    return () => clearTimeout(id)
  }, [reproduciendo, paso, total, velocidad])

  if (!datos) {
    return <aside className="recorrido-panel"><CargandoEsfera tamano={90} texto="Calculando recorrido..." /></aside>
  }

  const actual = paso > 0 ? datos.pasos[paso - 1] : null
  const esCola = tipo === 'bfs'
  const estructura = actual?.estructura ?? [datos.inicio]
  const parar = (n) => {
    setReproduciendo(false)
    setPaso(Math.max(0, Math.min(total, n)))
  }
  const alternar = () => {
    if (paso >= total) {
      setPaso(0)
      setReproduciendo(true)
    } else {
      setReproduciendo(!reproduciendo)
    }
  }

  return (
    <aside className="recorrido-panel">
      <div className="recorrido-titulo">
        <h2>{tipo.toUpperCase()}</h2>
        <span className="gris">paso {paso} de {total}</span>
      </div>
      <p className="recorrido-explicacion">{EXPLICACION[tipo]}</p>

      <div className="recorrido-botones">
        <button onClick={() => parar(0)} aria-label="Reiniciar" title="Reiniciar">⏮</button>
        <button onClick={() => parar(paso - 1)} aria-label="Paso anterior" title="Paso anterior">◀</button>
        <button className="principal" onClick={alternar}>
          {reproduciendo ? '❚❚ Pausa' : paso >= total ? '↻ Repetir' : '▶ Reproducir'}
        </button>
        <button onClick={() => parar(paso + 1)} aria-label="Paso siguiente" title="Paso siguiente">▶</button>
        <button onClick={() => parar(total)} aria-label="Ir al final" title="Ir al final">⏭</button>
      </div>
      <div className="recorrido-opciones">
        <div className="segmentado recorrido-velocidad">
          {VELOCIDADES.map((v, i) => (
            <button key={v.etiqueta} className={velocidad === i ? 'activo' : ''} onClick={() => setVelocidad(i)}>{v.etiqueta}</button>
          ))}
        </div>
        <button className="recorrido-sonido" onClick={cambiarSonido} aria-pressed={sonido} title={sonido ? 'Silenciar' : 'Activar sonido'}>
          {sonido ? '🔊 Sonido' : '🔇 Silencio'}
        </button>
      </div>

      <div className="recorrido-bloque" aria-live="polite">
        <h3>Ahora</h3>
        {actual ? (
          <p>
            Visita a <b className="amarillo">{nombreDe(actual.nodo)}</b>
            {actual.padre !== null ? <> desde <b>{nombreDe(actual.padre)}</b></> : ' (inicio de un componente)'}
          </p>
        ) : (
          <p className="gris">{grafoListo ? 'Pulsa reproducir o avanza paso a paso.' : 'Dibujando el grafo... el recorrido empieza en cuanto termine.'}</p>
        )}
        <p className="gris">
          Recorre solo la figura de <b>{datos.genero}</b>: los {total} usuarios conectados con el inicial. Las demás figuras no se tocan.
        </p>
      </div>

      <div className="recorrido-bloque">
        <h3>{esCola ? 'Cola (sale el de la izquierda)' : 'Pila (el tope es el de la derecha)'}</h3>
        <div className="recorrido-fichas">
          {estructura.length === 0
            ? <span className="gris">vacía</span>
            : estructura.map((id, i) => <span key={`${id}-${i}`} className="ficha">{nombreDe(id)}</span>)}
        </div>
      </div>

      <div className="recorrido-bloque recorrido-orden">
        <h3>Orden de visita</h3>
        <ol>
          {datos.pasos.slice(0, paso).map((p, i) => (
            <li key={p.nodo} className={i === paso - 1 ? 'actual' : ''}>{nombreDe(p.nodo)}</li>
          ))}
        </ol>
      </div>
    </aside>
  )
}
