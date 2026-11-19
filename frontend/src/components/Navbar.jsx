import { useEffect, useRef, useState } from 'react'
import Avatar from './Avatar'

export default function Navbar({ perfil, usuarios, vista, onVista, onPerfil, onSalir }) {
  const [abierto, setAbierto] = useState(false)
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

  return (
    <nav className={`navbar ${solida ? 'navbar-solida' : ''}`}>
      <div className="navbar-izq">
        <div className="logo">GRAFOFLIX</div>
        <button className={vista === 'inicio' ? 'activo' : ''} onClick={() => onVista('inicio')}>Inicio</button>
        <button className={vista === 'explorar' ? 'activo' : ''} onClick={() => onVista('explorar')}>Explorar</button>
        <button className={vista === 'grafo' ? 'activo' : ''} onClick={() => onVista('grafo')}>Grafos</button>
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
    </nav>
  )
}
