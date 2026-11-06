import { useEffect, useState } from 'react'
import { api } from '../api'
import { COLOR_GENERO } from '../colores'
import GrafoCanvas from './GrafoCanvas'

export default function GraphView({ perfilId, usuarios }) {
  const [modo, setModo] = useState('completo')
  const [subId, setSubId] = useState(perfilId)
  const [datos, setDatos] = useState({ nodes: [], links: [] })

  useEffect(() => {
    const pedir = modo === 'completo' ? api.grafo() : api.subGrafo(subId)
    pedir.then(setDatos)
  }, [modo, subId])

  const verSubGrafo = (id) => {
    setSubId(id)
    setModo('sub')
  }

  const totalUsuarios = datos.nodes.filter((n) => n.tipo === 'usuario').length
  const conexiones = datos.links.filter((l) => l.tipo === 'usuario').length

  return (
    <main className="grafo-pagina">
      <div className="grafo-cabecera">
        <div>
          <h1>Grafo de usuarios</h1>
          <p className="gris">
            Dos usuarios están conectados si comparten el mismo género favorito. Pasa el cursor sobre un nodo y haz clic en un usuario para ver su sub-grafo.
          </p>
        </div>
        <div className="grafo-controles">
          <div className="segmentado">
            <button className={modo === 'completo' ? 'activo' : ''} onClick={() => setModo('completo')}>Grafo completo</button>
            <button className={modo === 'sub' ? 'activo' : ''} onClick={() => setModo('sub')}>Sub-grafo</button>
          </div>
          {modo === 'sub' && (
            <select className="selector" value={subId} onChange={(e) => verSubGrafo(Number(e.target.value))}>
              {usuarios.map((u) => (
                <option key={u.id} value={u.id}>
                  {u.id}. {u.nombre} {u.apellido}{u.id === perfilId ? ' (tú)' : ''} — {u.genero_favorito ?? 'sin películas'}
                </option>
              ))}
            </select>
          )}
        </div>
      </div>

      <div className="grafo-lienzo">
        <GrafoCanvas
          datos={datos}
          destacadoId={modo === 'sub' ? subId : perfilId}
          onNodeClick={verSubGrafo}
        />
        <div className="grafo-stats">
          <span><b>{totalUsuarios}</b> usuarios</span>
          <span><b>{conexiones}</b> aristas entre usuarios</span>
        </div>
        <div className="leyenda">
          {Object.entries(COLOR_GENERO).map(([g, c]) => (
            <span key={g}><i style={{ background: c }} />{g}</span>
          ))}
        </div>
      </div>
    </main>
  )
}
