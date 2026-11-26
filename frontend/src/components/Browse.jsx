import { useEffect, useMemo, useRef, useState } from 'react'
import { api } from '../api'
import { colorGenero } from '../colores'
import Avatar from './Avatar'
import Grafo3D from './Grafo3D'
import MovieRow from './MovieRow'
import PerfilTarjeta from './PerfilTarjeta'
import MovieModal from './MovieModal'
import CargandoEsfera from './CargandoEsfera'

export default function Browse({ perfilId, onPerfil, onVerGrafo, onExplorar, onHistorial, onConexiones, onVisto }) {
  const [detalle, setDetalle] = useState(null)
  const [subGrafo, setSubGrafo] = useState({ nodes: [], links: [] })
  const [seleccion, setSeleccion] = useState(null)
  const [ancho, setAncho] = useState(window.innerWidth)
  const angosto = ancho < 860
  const compacto = ancho < 1024
  const movil = ancho < 768
  const mediano = ancho >= 1024 && ancho < 1260
  const hero = useRef(null)
  const heroIzq = useRef(null)
  // Fracción vertical libre arriba (navbar) y abajo (texto del perfil)
  const [vertical, setVertical] = useState({ arriba: 0, abajo: 0 })

  useEffect(() => {
    api.usuario(perfilId).then(setDetalle)
    api.subGrafo(perfilId).then(setSubGrafo)
    window.scrollTo(0, 0)
  }, [perfilId])

  useEffect(() => {
    const alCambiar = () => setAncho(window.innerWidth)
    window.addEventListener('resize', alCambiar)
    return () => window.removeEventListener('resize', alCambiar)
  }, [])

  // Entre 768 y 1023 px el grafo va centrado en el hueco que queda
  // entre la barra de navegación y el texto del perfil
  useEffect(() => {
    if (!hero.current || !heroIzq.current) return
    const medir = () => {
      const alto = hero.current.offsetHeight
      const libreArriba = 70 / alto
      const libreAbajo = (alto - heroIzq.current.offsetTop + 10) / alto
      setVertical({ arriba: libreArriba, abajo: Math.min(libreAbajo, 0.75) })
    }
    medir()
    const observador = new ResizeObserver(medir)
    observador.observe(hero.current)
    observador.observe(heroIzq.current)
    return () => observador.disconnect()
  }, [detalle !== null])

  const porGenero = useMemo(() => {
    if (!detalle) return []
    return Object.keys(detalle.generos).map((g) => [g, detalle.peliculas_vistas.filter((p) => p.genero === g)])
  }, [detalle])

  if (!detalle) return <div className="estado"><CargandoEsfera tamano={140} texto="Cargando perfil..." /></div>

  const destacada = detalle.recomendadas[0]
  const esVista = (p) => detalle.peliculas_vistas.some((v) => v.id === p.id)

  const ver = async (pelicula) => {
    const resultado = await api.ver(perfilId, pelicula.id)
    setDetalle(resultado.usuario)
    // Una película nueva puede cambiar sus conexiones (género o películas en común)
    if (resultado.nueva) {
      api.subGrafo(perfilId).then(setSubGrafo)
    }
    onVisto(resultado, pelicula)
  }

  return (
    <main>
      <header className="hero" ref={hero} style={{ '--hero-color': colorGenero(detalle.genero_favorito) }}>
        <div className="hero-grafo">
          <Grafo3D
            datos={subGrafo}
            destacadoId={perfilId}
            onNodeClick={(id) => id !== perfilId && onPerfil(id)}
            // Zona donde se encuadra el grafo:
            // >= 1024 px: pegado al borde derecho, a la derecha del texto
            // 768–1023 px: centrado a lo ancho, en el hueco sobre el texto
            // <   768 px: centrado en todo el hero, de fondo detrás del texto
            areaIzq={compacto ? 0 : 0.45}
            areaDer={compacto ? 0 : 0.03}
            areaArriba={compacto && !movil ? vertical.arriba : 0}
            // 1024–1259 px: un poco más arriba (abajo sobraba espacio
            // antes de los detalles del perfil)
            areaAbajo={compacto && !movil ? vertical.abajo : mediano ? 0.18 : 0}
            alinear={compacto ? 'centro' : 'derecha'}
            // 768–1023 px: 25% más grande; 1024–1259 px: 20% más grande
            escala={compacto && !movil ? 1.25 : mediano ? 1.2 : 1}
          />
        </div>

        <div className="hero-izq" ref={heroIzq}>
          <div className="hero-contenido">
            <p className="hero-etiqueta">Perfil de {detalle.nombre} {detalle.apellido}</p>
            <h1>{destacada ? destacada.titulo : 'Aún no has visto ninguna película'}</h1>
            {destacada ? (
              <p className="hero-texto">
                {/* Explicación del BFS: tú -> película en común -> otro usuario -> esta película */}
                {destacada.origen === 'bfs' ? (
                  <>Porque <strong>{destacada.explicacion.usuario}</strong> también vio <strong>{destacada.explicacion.pelicula}</strong>, como tú, y vio esta película
                    {destacada.usuarios_que_la_vieron > 1 ? ` (igual que otros ${destacada.usuarios_que_la_vieron - 1} usuarios cercanos)` : ''}.</>
                ) : (
                  <>Una de las películas más vistas en GrafoFlix ({destacada.puntaje} vistas).</>
                )}{' '}
                Dirigida por {destacada.director}, con {destacada.actores}.
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

          <PerfilTarjeta detalle={detalle} onHistorial={onHistorial} onConexiones={onConexiones} />
        </div>

      </header>

      <div className="filas">
        <MovieRow titulo="Recomendadas para ti" peliculas={detalle.recomendadas} bordeGenero onClick={setSeleccion} />
        {detalle.por_director?.nombre && (
          <MovieRow
            titulo={`Más de ${detalle.por_director.nombre}, que dirigió ${detalle.por_director.vistas} de tus películas`}
            peliculas={detalle.por_director.peliculas}
            onClick={setSeleccion}
          />
        )}
        {detalle.por_actor?.nombre && (
          <MovieRow
            titulo={`Con ${detalle.por_actor.nombre}, que aparece en ${detalle.por_actor.vistas} de tus películas`}
            peliculas={detalle.por_actor.peliculas}
            onClick={setSeleccion}
          />
        )}
        <MovieRow titulo="Populares en GrafoFlix" peliculas={detalle.populares ?? []} vertical onClick={setSeleccion} />
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
