import { useEffect, useState } from 'react'
import { api } from '../api'
import { COLOR_GENERO, colorGenero } from '../colores'
import Avatar from './Avatar'
import Grafo3D from './Grafo3D'
import CargandoEsfera from './CargandoEsfera'

const VACIO = { nodes: [], links: [] }

// Texto del motivo de una conexión (ver grafo.motivos_conexion)
const motivoTexto = (c) =>
  c.motivos
    .map((m) => (m === 'genero' ? `mismo género (${c.genero_favorito})` : `${c.peliculas_comunes} películas en común`))
    .join(' y ')

// Sub-grafo con todas las conexiones del usuario y la lista de por qué está conectado con cada uno
export default function Conexiones({ perfilId, onPerfil, onVolver }) {
  const [detalle, setDetalle] = useState(null)
  const [datos, setDatos] = useState(VACIO)
  const [grafoListo, setGrafoListo] = useState(false)
  const [reinicio, setReinicio] = useState(0)

  useEffect(() => {
    api.usuario(perfilId).then(setDetalle)
    api.conexiones(perfilId).then(setDatos)
    window.scrollTo(0, 0)
  }, [perfilId])

  if (!detalle) return <div className="estado"><CargandoEsfera tamano={140} texto="Cargando conexiones..." /></div>

  const conexiones = [...detalle.conexiones].sort((a, b) => b.peliculas_comunes - a.peliculas_comunes)
  const porGenero = conexiones.filter((c) => c.motivos.includes('genero')).length
  const porPeliculas = conexiones.filter((c) => c.motivos.includes('peliculas')).length

  return (
    <main className="grafo-pagina conexiones-pagina">
      <div className="grafo-cabecera">
        <div>
          <button className="historial-volver" onClick={onVolver}>‹ Volver al perfil</button>
          <h1>Conexiones de {detalle.nombre} {detalle.apellido}</h1>
          <p className="gris">
            {conexiones.length} conexiones en el grafo único: {porGenero} por compartir género favorito y {porPeliculas} por
            películas vistas en común. Haz clic en un usuario para ir a su perfil.
          </p>
        </div>
      </div>

      <div className="grafo-cuerpo con-panel">
        <div className="grafo-lienzo">
          {conexiones.length > 0 ? (
            <>
              <Grafo3D
                datos={datos}
                destacadoId={perfilId}
                onNodeClick={(id) => id !== perfilId && onPerfil(id)}
                interactivo
                reinicio={reinicio}
                onListo={setGrafoListo}
              />
              {!grafoListo && (
                <div className="grafo-cargando">
                  <CargandoEsfera tamano={130} texto="Dibujando el sub-grafo..." />
                </div>
              )}
              <button className="grafo-restablecer" onClick={() => setReinicio(reinicio + 1)} title="Volver a la vista inicial">
                ⟲ Restablecer vista
              </button>
              <div className="leyenda">
                {Object.entries(COLOR_GENERO).map(([g, c]) => (
                  <span key={g}><i style={{ background: c }} />{g}</span>
                ))}
              </div>
            </>
          ) : (
            <p className="estado">Todavía no tiene conexiones con otros usuarios.</p>
          )}
        </div>

        {conexiones.length > 0 && (
          <aside className="conexiones-lista">
            {conexiones.map((c) => (
              <button key={c.id} className="conexion-item" onClick={() => onPerfil(c.id)}>
                <Avatar usuario={c} tamano={40} />
                <div>
                  <strong>{c.nombre} {c.apellido}</strong>
                  <span className="gris">{motivoTexto(c)}</span>
                </div>
                <i style={{ background: colorGenero(c.genero_favorito) }} title={c.genero_favorito ?? 'sin género'} />
              </button>
            ))}
          </aside>
        )}
      </div>
    </main>
  )
}
