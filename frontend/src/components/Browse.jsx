import { useEffect, useMemo, useState } from 'react'
import { api } from '../api'
import { colorGenero } from '../colores'
import Avatar from './Avatar'
import GrafoCanvas from './GrafoCanvas'
import MovieRow from './MovieRow'
import MovieModal from './MovieModal'

export default function Browse({ perfilId, onPerfil, onVerGrafo, onExplorar, onVisto }) {
  const [detalle, setDetalle] = useState(null)
  const [subGrafo, setSubGrafo] = useState({ nodes: [], links: [] })
  const [seleccion, setSeleccion] = useState(null)
  const [angosto, setAngosto] = useState(window.innerWidth < 860)

  useEffect(() => {
    api.usuario(perfilId).then(setDetalle)
    api.subGrafo(perfilId).then(setSubGrafo)
    window.scrollTo(0, 0)
  }, [perfilId])

  useEffect(() => {
    const alCambiar = () => setAngosto(window.innerWidth < 860)
    window.addEventListener('resize', alCambiar)
    return () => window.removeEventListener('resize', alCambiar)
  }, [])

  const porGenero = useMemo(() => {
    if (!detalle) return []
    return Object.keys(detalle.generos).map((g) => [g, detalle.peliculas_vistas.filter((p) => p.genero === g)])
  }, [detalle])

  if (!detalle) return <div className="estado">Cargando perfil...</div>

  const destacada = detalle.recomendadas[0]
  const maximo = Math.max(1, ...Object.values(detalle.generos))
  const esVista = (p) => detalle.peliculas_vistas.some((v) => v.id === p.id)

  const ver = async (pelicula) => {
    const resultado = await api.ver(perfilId, pelicula.id)
    setDetalle(resultado.usuario)
    // Si cambió su género favorito, cambian sus conexiones
    if (resultado.nueva && resultado.genero_anterior !== resultado.usuario.genero_favorito) {
      api.subGrafo(perfilId).then(setSubGrafo)
    }
    onVisto(resultado, pelicula)
  }

  return (
    <main>
      <header className="hero" style={{ '--hero-color': colorGenero(detalle.genero_favorito) }}>
        <div className="hero-grafo">
          <GrafoCanvas
            datos={subGrafo}
            destacadoId={perfilId}
            onNodeClick={(id) => id !== perfilId && onPerfil(id)}
            areaIzq={angosto ? 0 : 0.45}
            interactivo={false}
            fondo="rgba(0,0,0,0)"
          />
        </div>

        <div className="hero-izq">
          <div className="hero-contenido">
            <p className="hero-etiqueta">Perfil de {detalle.nombre} {detalle.apellido}</p>
            <h1>{destacada ? destacada.titulo : 'Aún no has visto ninguna película'}</h1>
            {destacada ? (
              <p className="hero-texto">
                Porque tu género favorito es <strong>{detalle.genero_favorito}</strong>. Dirigida por {destacada.director}, con {destacada.actores}.
              </p>
            ) : (
              <p className="hero-texto">Empieza a ver películas para recibir recomendaciones.</p>
            )}
            <div className="hero-botones">
              {destacada && <button className="boton-blanco" onClick={() => setSeleccion(destacada)}>▶ Más información</button>}
              <button className="boton-gris" onClick={onExplorar}>Explorar películas</button>
              <button className="boton-gris" onClick={onVerGrafo}>Ver grafo completo</button>
            </div>
          </div>

          <aside className="perfil-tarjeta">
            <div className="perfil-tarjeta-cabecera">
              <Avatar usuario={detalle} tamano={56} />
              <div>
                <strong>{detalle.nombre} {detalle.apellido}</strong>
                <span className="gris">{detalle.correo}</span>
              </div>
              <div className="estadisticas">
                <div><b>{detalle.cantidad_vistas}</b><span>vistas</span></div>
                <div><b>{detalle.conexiones.length}</b><span>conexiones</span></div>
              </div>
            </div>
            <div className="barras">
              {Object.entries(detalle.generos).map(([g, n]) => (
                <div key={g} className="barra">
                  <span>{g}</span>
                  <div className="barra-pista"><div style={{ width: `${(n / maximo) * 100}%`, background: colorGenero(g) }} /></div>
                  <span className="gris">{n}</span>
                </div>
              ))}
            </div>
          </aside>
        </div>

        <p className="hero-grafo-etiqueta">
          Sub-grafo de {detalle.nombre}: {detalle.conexiones.length} {detalle.conexiones.length === 1 ? 'usuario' : 'usuarios'} con {detalle.genero_favorito ?? 'sin películas vistas'}
          {!angosto && ' · haz clic en un nodo para ir a su perfil'}
        </p>
      </header>

      <div className="filas">
        <MovieRow titulo="Recomendadas para ti" peliculas={detalle.recomendadas} onClick={setSeleccion} />
        <MovieRow titulo="Vistas recientemente" peliculas={detalle.peliculas_vistas} vistas onClick={setSeleccion} />
        {porGenero.map(([g, lista]) => (
          <MovieRow key={g} titulo={`Viste en ${g}`} peliculas={lista} vistas onClick={setSeleccion} />
        ))}

        {detalle.conexiones.length > 0 && (
          <section className="fila">
            <h2>Usuarios con tus mismos gustos</h2>
            <div className="conexiones">
              {detalle.conexiones.map((u) => (
                <button key={u.id} className="perfil perfil-chico" onClick={() => onPerfil(u.id)}>
                  <Avatar usuario={u} tamano={80} />
                  <span className="perfil-nombre">{u.nombre}</span>
                </button>
              ))}
            </div>
          </section>
        )}
      </div>

      <MovieModal pelicula={seleccion} vista={seleccion && esVista(seleccion)} onCerrar={() => setSeleccion(null)} onVer={ver} />
    </main>
  )
}
