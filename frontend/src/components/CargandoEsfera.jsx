import { useEffect, useRef } from 'react'
import * as THREE from 'three'

/**
 * Indicador de carga en three.js con el mismo estilo de los nodos del grafo:
 * una esfera de bolitas (espiral de Fibonacci) que gira y late, y tres
 * esferas pequeñas que orbitan a su alrededor dejando una estela.
 * tamano: lado del lienzo en píxeles. texto: leyenda opcional debajo.
 */

// Bolita difusa (centro brillante, borde transparente), igual que en Grafo3D
function texturaBolita() {
  const lienzo = document.createElement('canvas')
  lienzo.width = lienzo.height = 64
  const ctx = lienzo.getContext('2d')
  const g = ctx.createRadialGradient(32, 32, 0, 32, 32, 32)
  g.addColorStop(0, 'rgba(255,255,255,1)')
  g.addColorStop(0.4, 'rgba(255,255,255,0.8)')
  g.addColorStop(1, 'rgba(255,255,255,0)')
  ctx.fillStyle = g
  ctx.fillRect(0, 0, 64, 64)
  return new THREE.CanvasTexture(lienzo)
}

function esfera(cantidad, radio, color, tamano, textura) {
  const pos = new Float32Array(cantidad * 3)
  const dorado = Math.PI * (3 - Math.sqrt(5))
  for (let i = 0; i < cantidad; i++) {
    const phi = Math.acos(1 - (2 * (i + 0.5)) / cantidad)
    const theta = i * dorado
    pos[i * 3] = radio * Math.sin(phi) * Math.cos(theta)
    pos[i * 3 + 1] = radio * Math.cos(phi)
    pos[i * 3 + 2] = radio * Math.sin(phi) * Math.sin(theta)
  }
  const geo = new THREE.BufferGeometry()
  geo.setAttribute('position', new THREE.BufferAttribute(pos, 3))
  const mat = new THREE.PointsMaterial({
    size: tamano, map: textura, color, transparent: true, depthWrite: false, blending: THREE.AdditiveBlending,
  })
  return new THREE.Points(geo, mat)
}

// Colores de las órbitas: rojo de la marca, cian del árbol y amarillo del nodo actual
const ORBITAS = [
  { color: '#e50914', radio: 3.4, vel: 1.6, incl: 0.5 },
  { color: '#00f0ff', radio: 3.9, vel: -1.2, incl: -0.9 },
  { color: '#ffd23f', radio: 3.0, vel: 2.1, incl: 1.4 },
]
const ESTELA = 14

export default function CargandoEsfera({ tamano = 120, texto = '' }) {
  const lienzo = useRef(null)

  useEffect(() => {
    const renderer = new THREE.WebGLRenderer({ canvas: lienzo.current, alpha: true, antialias: true })
    renderer.setPixelRatio(Math.min(2, window.devicePixelRatio))
    renderer.setSize(tamano, tamano, false)
    const escena = new THREE.Scene()
    const camara = new THREE.PerspectiveCamera(40, 1, 0.1, 100)
    camara.position.z = 13
    const textura = texturaBolita()

    const nucleo = esfera(700, 2, '#ff3d47', 0.32, textura)
    escena.add(nucleo)

    // Cada órbita: una esfera pequeña y su estela de esferas cada vez más chicas
    const orbitas = ORBITAS.map((o) => {
      const plano = new THREE.Group()
      plano.rotation.x = o.incl
      plano.rotation.z = o.incl * 0.6
      const cola = Array.from({ length: ESTELA }, (_, i) => {
        const s = esfera(i === 0 ? 120 : 40, 0.42 * (1 - i / ESTELA) + 0.05, o.color, i === 0 ? 0.2 : 0.16, textura)
        s.material.opacity = 1 - i / ESTELA
        plano.add(s)
        return s
      })
      escena.add(plano)
      return { ...o, cola }
    })

    const quieto = window.matchMedia('(prefers-reduced-motion: reduce)').matches
    let cuadro
    const animar = () => {
      const t = performance.now() / 1000
      nucleo.rotation.y = t * 0.6
      nucleo.rotation.x = 0.4 * Math.sin(t * 0.7)
      nucleo.scale.setScalar(1 + 0.06 * Math.sin(t * 3))
      orbitas.forEach((o) => o.cola.forEach((s, i) => {
        const a = (t - i * 0.035) * o.vel * 2
        s.position.set(Math.cos(a) * o.radio, 0, Math.sin(a) * o.radio)
        s.rotation.y = t
      }))
      renderer.render(escena, camara)
      if (!quieto) cuadro = requestAnimationFrame(animar)
    }
    animar()

    return () => {
      cancelAnimationFrame(cuadro)
      escena.traverse((obj) => {
        obj.geometry?.dispose()
        obj.material?.dispose()
      })
      textura.dispose()
      renderer.dispose()
    }
  }, [tamano])

  return (
    <div className="cargando-esfera" role="status" aria-live="polite">
      <canvas ref={lienzo} style={{ width: tamano, height: tamano }} aria-hidden="true" />
      {texto && <span>{texto}</span>}
    </div>
  )
}
