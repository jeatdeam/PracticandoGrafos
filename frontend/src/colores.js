export const COLOR_GENERO = {
  'Acción': '#e50914',
  'Aventura': '#f5a524',
  'Comedia': '#f2d43d',
  'Drama': '#7b61ff',
  'Sci-Fi': '#1fb6ff',
  'Terror': '#a3122a',
  'Thriller': '#13c39c',
  'sin peliculas vistas': '#6b6b6b',
}

const AVATARES = ['#e50914', '#1fb6ff', '#f5a524', '#13c39c', '#7b61ff', '#ff4fa3']

export const colorGenero = (genero) => COLOR_GENERO[genero ?? 'sin peliculas vistas'] ?? '#6b6b6b'
export const colorAvatar = (id) => AVATARES[id % AVATARES.length]
