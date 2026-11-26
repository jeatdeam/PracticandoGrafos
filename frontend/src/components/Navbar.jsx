import { useEffect, useRef, useState } from 'react'
import { api } from '../api'
import Avatar from './Avatar'
import LogoFirma from './LogoFirma'

const CAMPOS = [
  ['', 'Todo'],
  ['titulo', 'Película'],
  ['director', 'Director'],
  ['actores', 'Actor'],
]

const PISTA = {
  '': 'Película, director o actor',
  titulo: 'Título de la película',
  director: 'Nombre del director',
  actores: 'Nombre del actor',
}

const TIPO = { director: 'Director', actores: 'Actor', titulo: 'Película' }

// Resalta en negrita la parte que coincide con lo escrito
function Resaltado({ texto, busqueda }) {
  const i = busqueda ? texto.toLowerCase().indexOf(busqueda.toLowerCase()) : -1
  if (i < 0) return texto
  return <>{texto.slice(0, i)}<b>{texto.slice(i, i + busqueda.length)}</b>{texto.slice(i + busqueda.length)}</>
}

function IconoBuscar() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" aria-hidden="true">
      <circle cx="11" cy="11" r="7" />
      <path d="m20 20-3.6-3.6" />
    </svg>
  )
}

export default function Navbar({ perfil, usuarios, vista, onVista, onPerfil, onSalir, onLogo, busqueda, onBuscar }) {
  const [abierto, setAbierto] = useState(false)
  const [buscando, setBuscando] = useState(Boolean(busqueda.texto))
  const entrada = useRef(null)
  const caja = useRef(null)
  // Lista desplegable: sugerencias del backend, si se ve y cuál está marcada con el teclado
  const [sugerencias, setSugerencias] = useState([])
  const [listaAbierta, setListaAbierta] = useState(false)
  const [marcada, setMarcada] = useState(-1)
  const [solida, setSolida] = useState(false)
  const menu = useRef(null)

  useEffect(() => {
    const alScroll = () => setSolida(window.scrollY > 40)
    window.addEventListener('scroll', alScroll)
    return () => window.removeEventListener('scroll', alScroll)
  }, [])

  // El menú se cierra con un clic fuera o con Escape (antes se cerraba al
  // cruzar el hueco entre el avatar y la lista con el ratón)
  useEffect(() => {
    if (!abierto) return
    const alClic = (e) => !menu.current?.contains(e.target) && setAbierto(false)
    const alTeclado = (e) => e.key === 'Escape' && setAbierto(false)
    document.addEventListener('pointerdown', alClic)
    document.addEventListener('keydown', alTeclado)
    return () => {
      document.removeEventListener('pointerdown', alClic)
      document.removeEventListener('keydown', alTeclado)
    }
  }, [abierto])

  // La caja se cierra al hacer clic fuera, salvo que tenga texto
  useEffect(() => {
    if (!buscando) return
    entrada.current?.focus()
    const alClic = (e) => {
      if (caja.current?.contains(e.target)) return
      setListaAbierta(false)
      if (!busqueda.texto) setBuscando(false)
    }
    document.addEventListener('pointerdown', alClic)
    return () => document.removeEventListener('pointerdown', alClic)
  }, [buscando, busqueda.texto])

  // Pide sugerencias al escribir (espera 120 ms entre teclas)
  useEffect(() => {
    if (!buscando) return
    let vigente = true
    const t = setTimeout(() => {
      api.sugerencias({ q: busqueda.texto.trim(), campo: busqueda.campo, usuario: perfil?.id })
        .then((lista) => {
          if (!vigente) return
          setSugerencias(lista)
          setMarcada(-1)
        })
        .catch(() => vigente && setSugerencias([]))
    }, 120)
    return () => {
      vigente = false
      clearTimeout(t)
    }
  }, [buscando, busqueda.texto, busqueda.campo, perfil?.id])

  const elegir = (s) => {
    onBuscar({ texto: s.texto, campo: s.campo })
    if (vista !== 'explorar') onVista('explorar')
    setListaAbierta(false)
  }

  const alTeclado = (e) => {
    if (e.key === 'Escape') {
      if (listaAbierta) setListaAbierta(false)
      else cerrarBusqueda()
    } else if (e.key === 'ArrowDown' && sugerencias.length) {
      e.preventDefault()
      setListaAbierta(true)
      setMarcada((m) => (m + 1) % sugerencias.length)
    } else if (e.key === 'ArrowUp' && sugerencias.length) {
      e.preventDefault()
      setMarcada((m) => (m <= 0 ? sugerencias.length - 1 : m - 1))
    } else if (e.key === 'Enter') {
      if (listaAbierta && marcada >= 0) elegir(sugerencias[marcada])
      else setListaAbierta(false)
    }
  }

  // Al escribir o cambiar el filtro se muestran los resultados en Explorar
  const buscar = (cambio) => {
    onBuscar({ ...busqueda, ...cambio })
    setListaAbierta(true)
    if (vista !== 'explorar') onVista('explorar')
  }

  const cerrarBusqueda = () => {
    onBuscar({ ...busqueda, texto: '' })
    setBuscando(false)
    setListaAbierta(false)
  }

  return (
    <nav className={`navbar ${solida ? 'navbar-solida' : ''}`}>
      <div className="navbar-izq">
        <button className="logo logo-lottie" onClick={onLogo} title="Volver al inicio (elegir cuántos usuarios)" aria-label="Grafoflix: volver al inicio">
          <LogoFirma variante="nav" />
        </button>
        <button className={vista === 'inicio' ? 'activo' : ''} onClick={() => onVista('inicio')}>Inicio</button>
        <button className={vista === 'explorar' ? 'activo' : ''} onClick={() => onVista('explorar')}>Explorar</button>
        <button className={vista === 'grafo' ? 'activo' : ''} onClick={() => onVista('grafo')}>Grafos</button>
      </div>
      <div className="navbar-der">
      <div className={`buscador-nav ${buscando ? 'abierto' : ''}`} ref={caja}>
        <button
          className="buscador-icono"
          onClick={() => { setBuscando(true); setListaAbierta(true) }}
          aria-label="Buscar películas"
          title="Buscar"
        >
          <IconoBuscar />
        </button>
        {buscando && (
          <>
            <input
              ref={entrada}
              type="search"
              placeholder={PISTA[busqueda.campo]}
              value={busqueda.texto}
              onChange={(e) => buscar({ texto: e.target.value })}
              onKeyDown={alTeclado}
              onFocus={() => setListaAbierta(true)}
              aria-label="Texto a buscar"
              role="combobox"
              aria-expanded={listaAbierta && sugerencias.length > 0}
              aria-controls="sugerencias-busqueda"
              aria-autocomplete="list"
            />
            <select value={busqueda.campo} onChange={(e) => buscar({ campo: e.target.value })} aria-label="Buscar por">
              {CAMPOS.map(([valor, texto]) => <option key={valor} value={valor}>{texto}</option>)}
            </select>
            {listaAbierta && sugerencias.length > 0 && (
              <ul className="sugerencias" id="sugerencias-busqueda" role="listbox">
                {sugerencias.map((s, i) => (
                  <li
                    key={`${s.campo}-${s.texto}`}
                    role="option"
                    aria-selected={i === marcada}
                    className={i === marcada ? 'marcada' : ''}
                    style={{ animationDelay: `${i * 25}ms` }}
                    // pointerdown en vez de click: así se elige antes de que el input pierda el foco
                    onPointerDown={(e) => { e.preventDefault(); elegir(s) }}
                    onMouseEnter={() => setMarcada(i)}
                  >
                    <span className={`sugerencia-tipo tipo-${s.campo}`}>{TIPO[s.campo]}</span>
                    <span className="sugerencia-texto"><Resaltado texto={s.texto} busqueda={busqueda.texto.trim()} /></span>
                    {s.recomendado && <span className="sugerencia-reco">recomendado</span>}
                  </li>
                ))}
              </ul>
            )}
          </>
        )}
      </div>
      {perfil && (
        <div className="navbar-perfil" ref={menu}>
          <button className="navbar-avatar" onClick={() => setAbierto(!abierto)}>
            <Avatar usuario={perfil} tamano={34} />
            <span className={`flecha ${abierto ? 'girada' : ''}`}>▾</span>
          </button>
          {abierto && (
            <div className="menu-perfil">
              {usuarios.filter((u) => u.id !== perfil.id).slice(0, 6).map((u) => (
                <button key={u.id} onClick={() => { onPerfil(u.id); setAbierto(false) }}>
                  <Avatar usuario={u} tamano={28} /> {u.nombre}
                </button>
              ))}
              <hr />
              <button onClick={onSalir}>Cambiar de perfil</button>
            </div>
          )}
        </div>
      )}
      </div>
    </nav>
  )
}
