// Sonidos del recorrido BFS/DFS generados con la Web Audio API (sin archivos).
// Cada visita es un "toque" corto tipo marimba: una onda base más un armónico
// agudo que se apaga rápido. Las notas salen de una escala pentatónica, que
// suena bien en cualquier orden.

let contexto = null
function audio() {
  if (!contexto) {
    const Ctx = window.AudioContext || window.webkitAudioContext
    if (!Ctx) return null
    contexto = new Ctx()
  }
  if (contexto.state === 'suspended') contexto.resume()
  return contexto
}

// Pentatónica de Do (Do, Re, Mi, Sol, La) en semitonos sobre Do4
const ESCALA = [0, 2, 4, 7, 9]
const DO4 = 261.63
const frecuencia = (grado) => {
  const octava = Math.floor(grado / ESCALA.length)
  const nota = ESCALA[((grado % ESCALA.length) + ESCALA.length) % ESCALA.length] + 12 * octava
  return DO4 * Math.pow(2, nota / 12)
}

function toque(hz, { volumen = 0.12, duracion = 0.45, retraso = 0 } = {}) {
  const ctx = audio()
  if (!ctx) return
  const t = ctx.currentTime + retraso
  const salida = ctx.createGain()
  salida.gain.setValueAtTime(0.0001, t)
  salida.gain.exponentialRampToValueAtTime(volumen, t + 0.008)
  salida.gain.exponentialRampToValueAtTime(0.0001, t + duracion)
  salida.connect(ctx.destination)

  // Onda base (cuerpo del sonido)
  const base = ctx.createOscillator()
  base.type = 'sine'
  base.frequency.value = hz
  base.connect(salida)

  // Armónico agudo que se apaga rápido (el "golpe" de la marimba)
  const brillo = ctx.createGain()
  brillo.gain.setValueAtTime(0.5, t)
  brillo.gain.exponentialRampToValueAtTime(0.0001, t + 0.09)
  brillo.connect(salida)
  const armonico = ctx.createOscillator()
  armonico.type = 'sine'
  armonico.frequency.value = hz * 4
  armonico.connect(brillo)

  base.start(t)
  armonico.start(t)
  base.stop(t + duracion + 0.05)
  armonico.stop(t + duracion + 0.05)
}

/**
 * Sonido al visitar un nodo.
 * indice: posición en el orden de visita (0, 1, 2...).
 * BFS sube por la escala (se expande); DFS baja (se adentra en profundidad).
 * inicio: el nodo inicial suena más grave y largo.
 */
export function sonarVisita(tipo, indice, inicio) {
  if (inicio) {
    toque(frecuencia(tipo === 'bfs' ? -5 : 5), { volumen: 0.16, duracion: 0.8 })
    return
  }
  // Recorre dos octavas y vuelve a empezar para no irse demasiado agudo/grave
  const paso = indice % 11
  const grado = tipo === 'bfs' ? paso : 10 - paso
  toque(frecuencia(grado))
}

/** Pequeño acorde (arpegio) al terminar el recorrido. */
export function sonarFin() {
  ;[0, 2, 4, 5].forEach((g, i) => toque(frecuencia(g), { volumen: 0.1, duracion: 0.9, retraso: i * 0.09 }))
}
