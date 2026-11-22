import Avatar from './Avatar'
import LogoFirma from './LogoFirma'

export default function ProfileSelect({ usuarios, onElegir, onConfigurar }) {
  return (
    <div className="perfiles">
      <button className="logo logo-grande logo-lottie" onClick={onConfigurar} title="Volver al inicio (elegir cuántos usuarios)" aria-label="Grafoflix: volver al inicio">
        <LogoFirma variante="grande" />
      </button>
      <h1>¿Quién está viendo ahora?</h1>
      <p className="perfiles-total">{usuarios.length} usuarios registrados</p>
      <div className="perfiles-grid">
        {usuarios.map((u) => (
          <button key={u.id} className="perfil" onClick={() => onElegir(u.id)}>
            <Avatar usuario={u} />
            <span className="perfil-nombre">{u.nombre}</span>
            <span className="perfil-meta">{u.cantidad_vistas} vistas</span>
          </button>
        ))}
      </div>
      <button className="boton-borde" onClick={onConfigurar}>
        Cambiar cantidad de usuarios
      </button>
    </div>
  )
}
