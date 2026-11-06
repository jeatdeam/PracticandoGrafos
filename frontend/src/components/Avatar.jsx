import { colorAvatar } from '../colores'

export default function Avatar({ usuario, tamano = 120 }) {
  return (
    <div
      className="avatar"
      style={{ width: tamano, height: tamano, background: colorAvatar(usuario.id), fontSize: tamano * 0.42 }}
    >
      {usuario.nombre[0]}
      {usuario.apellido[0]}
    </div>
  )
}
