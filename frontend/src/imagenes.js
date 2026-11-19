// Las películas son inventadas, así que cada una recibe una foto fija de
// picsum.photos usando su ID como semilla (siempre sale la misma foto).
export const imagenPelicula = (id, ancho, alto) =>
  `https://picsum.photos/seed/${encodeURIComponent(id)}/${ancho}/${alto}`

// Foto de perfil: misma idea; la semilla incluye el nombre para que al
// regenerar usuarios cada persona nueva reciba otra foto.
export const fotoUsuario = (usuario) =>
  imagenPelicula(`usuario-${usuario.id}-${usuario.nombre}-${usuario.apellido}`, 240, 240)

// Si la foto no carga, se oculta y queda el degradado del género de fondo.
export const ocultarSiFalla = (e) => { e.currentTarget.style.display = 'none' }
