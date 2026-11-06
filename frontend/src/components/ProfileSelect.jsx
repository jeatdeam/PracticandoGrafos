import Avatar from './Avatar'

export default function ProfileSelect({ usuarios, onElegir, onConfigurar }) {
  return (
    <div className="perfiles">
      <div className="logo logo-grande">GRAFOFLIX</div>
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
