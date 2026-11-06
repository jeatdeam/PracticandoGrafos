import { useEffect, useRef, useState } from 'react'
import ForceGraph2D from 'react-force-graph-2d'
import { colorGenero } from '../colores'

// Después de la simulación, source/target pasan de ser ids a objetos nodo
const extremos = (l) => [l.source.id ?? l.source, l.target.id ?? l.target]

/**
 * Dibuja un grafo de usuarios + géneros que ocupa todo su contenedor.
 * areaIzq: fracción del ancho (0 a 1) que se deja libre a la izquierda al encuadrar.
 * interactivo: permite zoom con la rueda y arrastrar el lienzo.
 */
export default function GrafoCanvas({ datos, destacadoId, onNodeClick, areaIzq = 0, interactivo = true, fondo = '#0b0b0b' }) {
  const contenedor = useRef(null)
  const grafo = useRef(null)
  const ajustado = useRef(false)
  const [tamano, setTamano] = useState(null)
  const [hover, setHover] = useState(null)

  useEffect(() => {
    const observador = new ResizeObserver(([e]) =>
      setTamano({ width: e.contentRect.width, height: e.contentRect.height }),
    )
    observador.observe(contenedor.current)
    return () => observador.disconnect()
  }, [])

  const montado = tamano !== null

  useEffect(() => {
    grafo.current?.d3Force('link').distance((l) => (l.tipo === 'genero' ? 50 : 90))
    grafo.current?.d3ReheatSimulation()
    ajustado.current = false
  }, [datos, montado])

  // Centra el grafo en la zona libre (a la derecha de areaIzq)
  const encuadrar = (ms) => {
    const caja = grafo.current?.getGraphBbox()
    if (!caja || !tamano) return
    const { width, height } = tamano
    const margen = 40
    const x0 = width * areaIzq + margen
    const x1 = width - margen
    const anchoCaja = caja.x[1] - caja.x[0] + 60
    const altoCaja = caja.y[1] - caja.y[0] + 60
    const zoom = Math.min((x1 - x0) / anchoCaja, (height - 2 * margen) / altoCaja, 2.2)
    const centroX = (caja.x[0] + caja.x[1]) / 2
    const centroY = (caja.y[0] + caja.y[1]) / 2
    grafo.current.zoom(zoom, ms)
    grafo.current.centerAt(centroX - ((x0 + x1) / 2 - width / 2) / zoom, centroY, ms)
  }

  useEffect(() => {
    if (ajustado.current) encuadrar(0)
  }, [tamano, areaIzq])

  const vecinos = new Set()
  if (hover) {
    vecinos.add(hover.id)
    datos.links.forEach((l) => {
      const [s, t] = extremos(l)
      if (s === hover.id) vecinos.add(t)
      if (t === hover.id) vecinos.add(s)
    })
  }

  const dibujarNodo = (nodo, ctx, escala) => {
    const esGenero = nodo.tipo === 'genero'
    const esDestacado = nodo.id === String(destacadoId)
    const radio = esGenero ? 11 : esDestacado ? 9 : 6
    const color = colorGenero(nodo.genero)

    ctx.globalAlpha = hover && !vecinos.has(nodo.id) ? 0.15 : 1
    ctx.beginPath()
    ctx.arc(nodo.x, nodo.y, radio, 0, 2 * Math.PI)
    ctx.fillStyle = esGenero ? color : '#1f1f1f'
    ctx.fill()
    ctx.lineWidth = esDestacado ? 3 : 2
    ctx.strokeStyle = esDestacado ? '#ffffff' : color
    ctx.stroke()

    ctx.font = `${esGenero || esDestacado ? 700 : 500} ${(esGenero ? 13 : 11) / escala}px Inter, sans-serif`
    ctx.textAlign = 'center'
    ctx.textBaseline = 'top'
    ctx.fillStyle = esGenero ? color : esDestacado ? '#ffffff' : '#d0d0d0'
    ctx.fillText(nodo.label, nodo.x, nodo.y + radio + 2)
    ctx.globalAlpha = 1
  }

  const colorArista = (l) => {
    const [s, t] = extremos(l)
    if (hover && s !== hover.id && t !== hover.id) return 'rgba(255,255,255,0.03)'
    return l.tipo === 'genero' ? 'rgba(31,182,255,0.7)' : 'rgba(255,255,255,0.25)'
  }

  return (
    <div className="grafo-canvas" ref={contenedor}>
      {montado && (
        <ForceGraph2D
          ref={grafo}
          width={tamano.width}
          height={tamano.height}
          graphData={datos}
          backgroundColor={fondo}
          nodeCanvasObject={dibujarNodo}
          nodePointerAreaPaint={(n, color, ctx) => {
            ctx.fillStyle = color
            ctx.beginPath()
            ctx.arc(n.x, n.y, 12, 0, 2 * Math.PI)
            ctx.fill()
          }}
          linkColor={colorArista}
          linkWidth={(l) => (l.tipo === 'genero' ? 1.5 : 0.8)}
          onNodeHover={setHover}
          onNodeClick={(n) => n.tipo === 'usuario' && onNodeClick?.(Number(n.id))}
          enableZoomInteraction={interactivo}
          enablePanInteraction={interactivo}
          warmupTicks={40}
          cooldownTicks={120}
          onEngineStop={() => {
            if (!ajustado.current) encuadrar(500)
            ajustado.current = true
          }}
        />
      )}
    </div>
  )
}
