import { colorGenero } from '../colores'
import Avatar from './Avatar'

// Tarjeta del usuario: vistas, conexiones y cuántas películas vio de cada género.
// Se usa en el perfil (Inicio) y en "Ya las viste" de Explorar, así al ver una
// película en cualquiera de los dos se actualiza igual.
export default function PerfilTarjeta({ detalle, onHistorial, onConexiones, className = '' }) {
  const maximo = Math.max(1, ...Object.values(detalle.generos))
  return (
    <aside className={`perfil-tarjeta ${className}`}>
      <div className="perfil-tarjeta-cabecera">
        <Avatar usuario={detalle} tamano={56} />
        <div>
          <strong>{detalle.nombre} {detalle.apellido}</strong>
          <span className="gris">{detalle.correo}</span>
        </div>
        <div className="estadisticas">
          <button type="button" onClick={onHistorial} title="Ver todas sus películas vistas por género">
            {/* key: al cambiar el número se repite la animación */}
            <b key={detalle.cantidad_vistas} className="numero-cambia">{detalle.cantidad_vistas}</b><span>vistas</span>
          </button>
          <button type="button" onClick={onConexiones} title="Ver sus conexiones como sub-grafo">
            <b key={detalle.conexiones.length} className="numero-cambia">{detalle.conexiones.length}</b><span>conexiones</span>
          </button>
        </div>
      </div>
      {Object.keys(detalle.generos).length > 0 && (
        <div className="barras">
          {Object.entries(detalle.generos).map(([g, n]) => (
            <div key={g} className="barra">
              <span>{g}</span>
              <div className="barra-pista"><div style={{ width: `${(n / maximo) * 100}%`, background: colorGenero(g) }} /></div>
              <span key={n} className="gris numero-cambia">{n}</span>
            </div>
          ))}
        </div>
      )}
    </aside>
  )
}
