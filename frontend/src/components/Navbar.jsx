import { useEffect, useState } from 'react'
import Avatar from './Avatar'

export default function Navbar({ perfil, usuarios, vista, onVista, onPerfil, onSalir }) {
  const [abierto, setAbierto] = useState(false)
  const [solida, setSolida] = useState(false)

  useEffect(() => {
    const alScroll = () => setSolida(window.scrollY > 40)
    window.addEventListener('scroll', alScroll)
    return () => window.removeEventListener('scroll', alScroll)
  }, [])

  return (
    <nav className={`navbar ${solida ? 'navbar-solida' : ''}`}>
      <div className="navbar-izq">
        <div className="logo">GRAFOFLIX</div>
        <button className={vista === 'inicio' ? 'activo' : ''} onClick={() => onVista('inicio')}>Inicio</button>
        <button className={vista === 'explorar' ? 'activo' : ''} onClick={() => onVista('explorar')}>Explorar</button>
        <button className={vista === 'grafo' ? 'activo' : ''} onClick={() => onVista('grafo')}>Grafos</button>
      </div>
      {perfil && (
        <div className="navbar-perfil" onMouseLeave={() => setAbierto(false)}>
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
