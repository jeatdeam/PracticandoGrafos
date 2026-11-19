import { useEffect, useMemo, useState } from 'react'
import { api } from '../api'
import { COLOR_GENERO } from '../colores'
import Grafo3D from './Grafo3D'
import RecorridoPanel from './RecorridoPanel'

// Mismo nombre que usa el backend para quien aún no vio películas
const SIN_GENERO = 'sin peliculas vistas'

export default function GraphView({ perfilId, usuarios }) {
  const [modo, setModo] = useState('completo')
  const [subId, setSubId] = useState(perfilId)
  const [inicioId, setInicioId] = useState(perfilId)
  const [datos, setDatos] = useState({ nodes: [], links: [] })
  // Recorrido BFS/DFS: pasos que devuelve el backend y cuántos se muestran
  const [pasos, setPasos] = useState(null)
  const [paso, setPaso] = useState(0)
  // Cada clic en "Restablecer vista" suma 1 y el grafo vuelve a su encuadre
  const [reinicio, setReinicio] = useState(0)
  // Género elegido en la lista de géneros ('' = todos): en el grafo completo
  // agranda su figura; en sub-grafo/BFS/DFS salta a un usuario de ese género
  const [generoFiltro, setGeneroFiltro] = useState('')

  const esRecorrido = modo === 'bfs' || modo === 'dfs'
  const esSub = modo === 'sub'

  // BFS y DFS recorren el grafo completo
  useEffect(() => {
    const pedir = esSub ? api.subGrafo(subId) : api.grafo()
    pedir.then(setDatos)
  }, [esSub, subId])

  useEffect(() => {
    setPasos(null)
    setPaso(0)
    if (esRecorrido) api.recorrido(modo, inicioId).then(setPasos)
  }, [modo, inicioId])

  // El recorrido se hace solo sobre la figura (género) del usuario inicial
  const generoInicio = usuarios.find((u) => u.id === inicioId)?.genero_favorito ?? SIN_GENERO

  // En BFS/DFS solo se muestra la figura que se recorre: su género y sus
  // usuarios. Se copian los nodos para no tocar los del grafo completo.
  const datosVista = useMemo(() => {
    if (!esRecorrido) return datos
    const nodes = datos.nodes.filter((n) => n.genero === generoInicio).map((n) => ({ id: n.id, label: n.label, tipo: n.tipo, genero: n.genero }))
    const ids = new Set(nodes.map((n) => n.id))
    const id = (x) => (typeof x === 'object' ? x.id : x)
    const links = datos.links
      .filter((l) => ids.has(id(l.source)) && ids.has(id(l.target)))
      .map((l) => ({ source: id(l.source), target: id(l.target), tipo: l.tipo }))
    return { nodes, links }
  }, [datos, esRecorrido, generoInicio])

  // Estado del grafo en el paso actual: figura recorrida, orden de visita,
  // nodo actual y aristas del árbol (padre -> hijo) ya recorridas
  const estado = useMemo(() => {
    if (!esRecorrido) return null
    const visitados = new Map()
    const arbol = new Set()
    ;(pasos?.pasos ?? []).slice(0, paso).forEach((p, i) => {
      visitados.set(String(p.nodo), i + 1)
      if (p.padre !== null) arbol.add(`${p.padre}-${p.nodo}`)
    })
    const actual = pasos && paso > 0 ? String(pasos.pasos[paso - 1].nodo) : null
    return { genero: pasos?.genero ?? generoInicio, visitados, arbol, actual }
  }, [esRecorrido, pasos, paso, generoInicio])

  const generoDe = (u) => u.genero_favorito ?? SIN_GENERO
  const generos = useMemo(() => {
    const cuenta = new Map()
    usuarios.forEach((u) => cuenta.set(generoDe(u), (cuenta.get(generoDe(u)) ?? 0) + 1))
    return [...cuenta].sort((a, b) => a[0].localeCompare(b[0]))
  }, [usuarios])

  // Al elegir un género en sub-grafo/BFS/DFS, si el usuario elegido no es de
  // ese género se salta al primero que sí lo es
  const elegirGenero = (genero) => {
    setGeneroFiltro(genero)
    if (!genero || modo === 'completo') return
    const elegido = esSub ? subId : inicioId
    if (usuarios.find((u) => u.id === elegido && generoDe(u) === genero)) return
    const primero = usuarios.find((u) => generoDe(u) === genero)
    if (primero) (esSub ? setSubId : setInicioId)(primero.id)
  }

  const verSubGrafo = (id) => {
    setSubId(id)
    setModo('sub')
  }

  const totalUsuarios = datosVista.nodes.filter((n) => n.tipo === 'usuario').length
  const conexiones = datosVista.links.filter((l) => l.tipo === 'usuario').length
  const nombreDe = (id) => usuarios.find((u) => u.id === id)?.nombre ?? id

  return (
    <main className="grafo-pagina">
      <div className="grafo-cabecera">
        <div>
          <h1>Grafo de usuarios</h1>
          <p className="gris">
            {esRecorrido
              ? `Recorrido ${modo.toUpperCase()} sobre la figura de ${generoInicio}: solo se muestra y se recorre esa figura. Haz clic en un usuario para empezar desde él, o elige en la lista a alguien de otro género para recorrer su figura.`
              : 'Dos usuarios están conectados si comparten el mismo género favorito. Arrastra para girar y usa la rueda para acercar. Haz clic en una figura para agrandarla; con ella agrandada, clic en un usuario para ver su sub-grafo o clic fuera para volver.'}
          </p>
        </div>
        <div className="grafo-controles">
          <div className="segmentado">
            <button className={modo === 'completo' ? 'activo' : ''} onClick={() => setModo('completo')}>Grafo completo</button>
            <button className={modo === 'sub' ? 'activo' : ''} onClick={() => setModo('sub')}>Sub-grafo</button>
            <button className={modo === 'bfs' ? 'activo' : ''} onClick={() => setModo('bfs')}>BFS</button>
            <button className={modo === 'dfs' ? 'activo' : ''} onClick={() => setModo('dfs')}>DFS</button>
          </div>
          {/* Lista de todos los usuarios: en grafo completo o sub-grafo abre el
              sub-grafo del elegido; en BFS/DFS lo usa como nodo inicial */}
          <select
            className="selector"
            // En el grafo completo muestra al usuario del perfil del que venimos
            value={esSub ? subId : esRecorrido ? inicioId : perfilId}
            onChange={(e) => (esRecorrido ? setInicioId : verSubGrafo)(Number(e.target.value))}
            aria-label={esRecorrido ? 'Usuario inicial del recorrido' : 'Buscar el sub-grafo de un usuario'}
          >
            {usuarios.map((u) => (
                <option key={u.id} value={u.id}>
                {esRecorrido ? 'Inicio: ' : ''}{u.id}. {u.nombre} {u.apellido}{u.id === perfilId ? ' (tú)' : ''} — {u.genero_favorito ?? 'sin películas'}
              </option>
            ))}
          </select>
          <select
            className="selector"
            value={generoFiltro}
            onChange={(e) => elegirGenero(e.target.value)}
            aria-label="Filtrar por género"
          >
            <option value="">Todos los géneros</option>
            {generos.map(([g, n]) => (
              <option key={g} value={g}>{g === SIN_GENERO ? 'Sin películas' : g} ({n})</option>
            ))}
          </select>
        </div>
      </div>

      <div className={`grafo-cuerpo ${esRecorrido ? 'con-panel' : ''}`}>
        <div className="grafo-lienzo">
          <Grafo3D
            datos={datosVista}
            destacadoId={esSub ? subId : esRecorrido ? inicioId : perfilId}
            onNodeClick={esRecorrido ? setInicioId : verSubGrafo}
            interactivo
            recorrido={estado}
            reinicio={reinicio}
            enfocarGenero={modo === 'completo' ? generoFiltro : ''}
            // El grafo completo se muestra un 50% más grande
            escala={modo === 'completo' ? 1.5 : 1}
          />
          <button className="grafo-restablecer" onClick={() => setReinicio(reinicio + 1)} title="Volver a la vista inicial">
            ⟲ Restablecer vista
          </button>
          <div className="grafo-stats">
            <span><b>{totalUsuarios}</b> usuarios</span>
            <span><b>{conexiones}</b> aristas entre usuarios</span>
          </div>
          {esRecorrido ? (
            <div className="leyenda">
              <span><i style={{ background: '#ffd23f' }} />Actual</span>
              <span><i style={{ background: '#e0e0e0' }} />Visitado (con su número de orden)</span>
              <span><i style={{ background: '#5a5a5a' }} />Sin visitar</span>
              <span><i style={{ background: 'radial-gradient(circle, #00f0ff 30%, transparent 32%) 0 0 / 4px 4px', width: 18, height: 4, borderRadius: 0 }} />Arista del árbol (puntos)</span>
            </div>
          ) : (
            <div className="leyenda">
              {Object.entries(COLOR_GENERO).map(([g, c]) => (
                <span key={g}><i style={{ background: c }} />{g}</span>
              ))}
            </div>
          )}
        </div>
        {esRecorrido && (
          <RecorridoPanel tipo={modo} datos={pasos} paso={paso} setPaso={setPaso} nombreDe={nombreDe} />
        )}
      </div>
    </main>
  )
}
