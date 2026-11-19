import { colorAvatar } from '../colores'
import { fotoUsuario, ocultarSiFalla } from '../imagenes'

// Foto de picsum encima; si no carga, quedan las iniciales sobre el color
export default function Avatar({ usuario, tamano = 120 }) {
  return (
    <div
      className="avatar"
      style={{ width: tamano, height: tamano, background: colorAvatar(usuario.id), fontSize: tamano * 0.42 }}
    >
      {usuario.nombre[0]}
      {usuario.apellido[0]}
      <img className="avatar-foto" src={fotoUsuario(usuario)} alt="" loading="lazy" decoding="async" onError={ocultarSiFalla} />
    </div>
  )
}
