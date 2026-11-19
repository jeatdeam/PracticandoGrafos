import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import ForceGraph3D from 'react-force-graph-3d'
import * as THREE from 'three'
import SpriteText from 'three-spritetext'
import { colorAvatar, colorGenero } from '../colores'

/**
 * Sub-grafo del usuario en 3D (three.js).
 * Cada nodo es una nube de bolitas que forma una esfera sin borde sólido:
 * las bolitas se concentran en el centro y se van dispersando hacia afuera.
 * - Género: nube grande en el centro con el nombre del género en medio.
 * - Usuarios: nubes pequeñas con el color de su avatar y su nombre debajo.
 * - Usuario del perfil: nube blanca algo más grande.
 * areaIzq / areaDer: fracción del ancho (0 a 1) libre a la izquierda/derecha.
 * areaArriba / areaAbajo: fracción del alto (0 a 1) libre arriba/abajo.
 * alinear: 'centro' (en la zona libre) o 'derecha' (pegado al borde derecho).
 * escala: agranda el grafo (1.25 = 25% más grande).
 * interactivo: permite zoom con la rueda y mover la vista (pestaña de grafos).
 *   El lienzo siempre ocupa todo el contenedor (así nada se corta al girar);
 *   el grafo se desplaza hacia la zona libre moviendo la vista de la cámara.
 */

// Textura de una bolita difusa (centro brillante, borde transparente)
let texturaBolita = null
function bolita() {
  if (texturaBolita) return texturaBolita
  const lienzo = document.createElement('canvas')
  lienzo.width = lienzo.height = 64
  const ctx = lienzo.getContext('2d')
  const g = ctx.createRadialGradient(32, 32, 0, 32, 32, 32)
  g.addColorStop(0, 'rgba(255,255,255,1)')
  g.addColorStop(0.4, 'rgba(255,255,255,0.8)')
  g.addColorStop(1, 'rgba(255,255,255,0)')
  ctx.fillStyle = g
  ctx.fillRect(0, 0, 64, 64)
  texturaBolita = new THREE.CanvasTexture(lienzo)
  return texturaBolita
}

// Bolitas repartidas dentro de una esfera, más densas en el centro.
// Cada una guarda su órbita (radio, ángulos, velocidad y fase) para que
// animarNube() la mueva por su cuenta dentro de la nube.
function nube(cantidad, radio, color, tamano) {
  const posiciones = new Float32Array(cantidad * 3)
  const orbitas = new Float32Array(cantidad * 5)
  for (let i = 0; i < cantidad; i++) {
    orbitas[i * 5] = radio * Math.pow(Math.random(), 0.75) // radio
    orbitas[i * 5 + 1] = Math.random() * Math.PI * 2 // ángulo horizontal
    orbitas[i * 5 + 2] = Math.acos(2 * Math.random() - 1) // inclinación
    orbitas[i * 5 + 3] = (0.25 + Math.random() * 0.6) * (Math.random() < 0.5 ? -1 : 1) // velocidad
    orbitas[i * 5 + 4] = Math.random() * Math.PI * 2 // fase
  }
  const geometria = new THREE.BufferGeometry()
  geometria.setAttribute('position', new THREE.BufferAttribute(posiciones, 3))
  const material = new THREE.PointsMaterial({
    size: tamano,
    map: bolita(),
    color,
    transparent: true,
    depthWrite: false,
    blending: THREE.AdditiveBlending,
  })
  const puntos = new THREE.Points(geometria, material)
  puntos.userData.orbitas = orbitas
  // Las bolitas se mueven, así que no se recorta la nube por su caja inicial
  puntos.frustumCulled = false
  animarNube(puntos, 0)
  return puntos
}

// Cada bolita orbita alrededor del centro de su nube, sube y baja un poco
// y se acerca/aleja (la nube "respira"), así la figura nunca está quieta
function animarNube(puntos, t) {
  const orbitas = puntos.userData.orbitas
  const posiciones = puntos.geometry.attributes.position
  const arr = posiciones.array
  for (let i = 0; i < arr.length / 3; i++) {
    const r0 = orbitas[i * 5]
    const fase = orbitas[i * 5 + 4]
    const r = r0 * (1 + 0.16 * Math.sin(t * 1.3 + fase))
    const theta = orbitas[i * 5 + 1] + orbitas[i * 5 + 3] * t
    const phi = orbitas[i * 5 + 2] + 0.35 * Math.sin(t * 0.7 + fase)
    arr[i * 3] = r * Math.sin(phi) * Math.cos(theta)
    arr[i * 3 + 1] = r * Math.cos(phi)
    arr[i * 3 + 2] = r * Math.sin(phi) * Math.sin(theta)
  }
  posiciones.needsUpdate = true
}

function texto(contenido, alto, color, negrita) {
  const sprite = new SpriteText(contenido, alto, color)
  sprite.fontFace = 'Inter, sans-serif'
  sprite.fontWeight = negrita ? '800' : '600'
  // Siempre visible por encima de las bolitas
  sprite.material.depthTest = false
  sprite.renderOrder = 10
  return sprite
}

const sinEtiqueta = () => ''

export default function Grafo3D({ datos, destacadoId, onNodeClick, areaIzq = 0, areaDer = 0, areaArriba = 0, areaAbajo = 0, alinear = 'centro', escala = 1, interactivo = false }) {
  const contenedor = useRef(null)
  const grafo = useRef(null)
  const ajustado = useRef(false)
  const ticks = useRef(0)
  const [tamano, setTamano] = useState(null)
  // El grafo queda invisible mientras se acomoda y aparece ya encuadrado
  const [listo, setListo] = useState(false)
  // Quien pidió reducir el movimiento en su sistema ve el grafo quieto
  const moverse = !window.matchMedia('(prefers-reduced-motion: reduce)').matches

  useEffect(() => {
    const observador = new ResizeObserver(([e]) =>
      setTamano({ width: e.contentRect.width, height: e.contentRect.height }),
    )
    observador.observe(contenedor.current)
    return () => observador.disconnect()
  }, [])

  const montado = tamano !== null && tamano.width > 0

  // El género queda fijo en el centro; los usuarios giran a su alrededor
  // Con un solo género (sub-grafo) éste queda fijo en el centro y los
  // usuarios giran a su alrededor; con varios (grafo completo) todos se mueven
  const datosGrafo = useMemo(() => {
    const generos = datos.nodes.filter((n) => n.tipo === 'genero')
    if (generos.length === 1) generos[0].fx = generos[0].fy = generos[0].fz = 0
    return datos
  }, [datos])

  // Color de cada género por id de nodo, para pintar sus aristas
  const colorPorNodo = useMemo(
    () => new Map(datos.nodes.filter((n) => n.tipo === 'genero').map((n) => [n.id, colorGenero(n.genero)])),
    [datos],
  )

  // Con muchos usuarios cada nube lleva menos bolitas para que no vaya lento
  const totalUsuarios = datos.nodes.filter((n) => n.tipo === 'usuario').length
  const factorBolitas = Math.min(1, 40 / Math.max(1, totalUsuarios))

  // Cámara: gira sola; se puede rotar arrastrando, pero sin zoom con la
  // rueda para no robarle el scroll a la página.
  useEffect(() => {
    const controles = grafo.current?.controls()
    if (!controles) return
    controles.enableZoom = interactivo
    controles.enablePan = interactivo
    controles.autoRotate = moverse
    controles.autoRotateSpeed = 0.8
  }, [montado, moverse, interactivo])

  // Fuerzas: distancias que dejan espacio entre nubes y una "flotación"
  // senoidal que no depende de alpha (no se apaga nunca).
  useEffect(() => {
    if (!montado || !grafo.current) return
    grafo.current.d3Force('link').distance((l) => (l.tipo === 'genero' ? 38 : 48))
    grafo.current.d3Force('charge').strength(-60)
    if (moverse) {
      let nodos = []
      const flotar = () => {
        const t = performance.now() / 1000
        for (const n of nodos) {
          n.vx += Math.cos(t * n.velFlotar + n.faseFlotar) * 0.04
          n.vy += Math.sin(t * n.velFlotar * 0.8 + n.faseFlotar) * 0.04
          n.vz += Math.sin(t * n.velFlotar * 0.6 + n.faseFlotar * 2) * 0.04
        }
      }
      flotar.initialize = (lista) => {
        nodos = lista
        nodos.forEach((n) => {
          n.faseFlotar ??= Math.random() * Math.PI * 2
          n.velFlotar ??= 0.5 + Math.random() * 0.5
        })
      }
      grafo.current.d3Force('flotar', flotar)
    } else {
      grafo.current.d3Force('flotar', null)
    }
    grafo.current.d3ReheatSimulation()
    ajustado.current = false
    ticks.current = 0
    setListo(false)
  }, [datosGrafo, montado, moverse])

  // Desplaza la imagen hacia el centro de la zona libre sin achicar el lienzo
  // Aleja la cámara lo justo para que la esfera que envuelve al grafo
  // (con nubes y nombres) quepa en la zona libre desde cualquier ángulo, y
  // desplaza la vista (sin achicar el lienzo) para ubicarlo en esa zona:
  // alinear="centro" lo centra; alinear="derecha" lo pega al borde derecho.
  const encuadrar = (ms = 800) => {
    const camara = grafo.current?.camera()
    if (!camara || !tamano) return
    const radio = Math.max(20, ...datosGrafo.nodes.map((n) => Math.hypot(n.x ?? 0, n.y ?? 0, n.z ?? 0))) + 16
    const tanV = Math.tan((camara.fov * Math.PI) / 360)
    const fraccionV = Math.max(0.25, 1 - areaArriba - areaAbajo)
    const fraccionH = Math.max(0.2, 1 - areaIzq - areaDer)
    const alto = tanV * fraccionV
    const anchoVisible = tanV * (tamano.width / tamano.height) * fraccionH
    // / 1.2: el grafo se ve un 20% más grande que el encuadre "seguro"
    const distancia = (radio / Math.min(alto, anchoVisible)) * 1.08 / 1.2 / escala

    const { width, height } = tamano
    // Radio del grafo en píxeles (sin el 20% extra, que solo agranda)
    const radioPx = (radio / (distancia * tanV)) * (height / 2) / 1.2
    const centroX = alinear === 'derecha'
      ? Math.max((1 - areaDer) * width - radioPx, ((areaIzq + 1 - areaDer) / 2) * width)
      : ((areaIzq + 1 - areaDer) / 2) * width
    const dx = centroX - width / 2
    const dy = ((areaArriba + 1 - areaAbajo) / 2 - 0.5) * height
    camara.setViewOffset(width, height, -dx, -dy, width, height)
    camara.updateProjectionMatrix()
    const p = camara.position
    const largo = Math.hypot(p.x, p.y, p.z) || 1
    grafo.current.cameraPosition(
      { x: (p.x / largo) * distancia, y: (p.y / largo) * distancia, z: (p.z / largo) * distancia },
      { x: 0, y: 0, z: 0 },
      ms,
    )
  }

  // Bucle propio para mover las bolitas dentro de cada nube, independiente
  // del motor de fuerzas (así no se congelan si este se detiene)
  useEffect(() => {
    if (!moverse) return
    let cuadro
    const animar = () => {
      const t = performance.now() / 1000
      datosGrafo.nodes.forEach((n) => n.__nube && animarNube(n.__nube, t))
      cuadro = requestAnimationFrame(animar)
    }
    cuadro = requestAnimationFrame(animar)
    return () => cancelAnimationFrame(cuadro)
  }, [datosGrafo, moverse])

  const mostrar = () => {
    encuadrar(0)
    ajustado.current = true
    setListo(true)
  }

  // Si cambia el tamaño de la ventana, se vuelve a encuadrar
  useEffect(() => {
    if (ajustado.current) encuadrar(0)
  }, [tamano, areaIzq, areaDer, areaArriba, areaAbajo, alinear, escala])

  const objetoNodo = useCallback((n) => {
    const esGenero = n.tipo === 'genero'
    const esDestacado = n.id === String(destacadoId)
    const radio = esGenero ? 10 : esDestacado ? 6 : 4.5
    const color = esGenero ? colorGenero(n.genero) : esDestacado ? '#ffffff' : colorAvatar(Number(n.id))
    const grupo = new THREE.Group()

    const cantidad = esGenero ? 650 : Math.round((esDestacado ? 260 : 170) * Math.max(factorBolitas, esDestacado ? 0.5 : 0.25))
    const puntos = nube(cantidad, radio, color, esGenero ? 1.3 : 1)
    grupo.add(puntos)
    n.__nube = puntos

    // Esfera invisible para poder hacer clic sobre la nube
    grupo.add(new THREE.Mesh(
      new THREE.SphereGeometry(radio, 12, 12),
      new THREE.MeshBasicMaterial({ transparent: true, opacity: 0, depthWrite: false }),
    ))

    if (esGenero) {
      grupo.add(texto(n.label, 4.2, '#ffffff', true))
    } else {
      // La etiqueta viene como "Ariel-0"; mostramos solo el nombre
      const nombre = texto(n.label.replace(/-\d+$/, ''), esDestacado ? 3.2 : 2.6, esDestacado ? '#ffffff' : '#d8d8d8', esDestacado)
      nombre.position.y = -(radio + 3)
      grupo.add(nombre)
    }
    return grupo
  }, [destacadoId, factorBolitas])

  const colorArista = useCallback((l) => {
    if (l.tipo !== 'genero') return '#ffffff'
    const extremo = (x) => (typeof x === 'object' ? x.id : x)
    return colorPorNodo.get(extremo(l.target)) ?? colorPorNodo.get(extremo(l.source)) ?? '#ffffff'
  }, [colorPorNodo])

  return (
    <div className={`grafo-canvas grafo-3d ${listo ? 'listo' : ''}`} ref={contenedor}>
      {montado && (
        <ForceGraph3D
          ref={grafo}
          width={tamano.width}
          height={tamano.height}
          graphData={datosGrafo}
          backgroundColor="rgba(0,0,0,0)"
          showNavInfo={false}
          controlType="orbit"
          nodeLabel={sinEtiqueta}
          nodeThreeObject={objetoNodo}
          linkColor={colorArista}
          linkOpacity={0.16}
          linkWidth={0}
          onNodeClick={(n) => n.tipo === 'usuario' && onNodeClick?.(Number(n.id))}
          warmupTicks={60}
          cooldownTicks={moverse ? Infinity : 120}
          // Por defecto la librería detiene el motor a los 15 s; si flota, nunca
          cooldownTime={moverse ? Infinity : 15000}
          d3AlphaMin={moverse ? 0 : 0.001}
          onEngineTick={() => {
            // Tras ~80 cuadros la estructura ya tomó su tamaño: se encuadra
            // al instante (sin animación) y recién entonces se muestra
            if (ajustado.current) return
            ticks.current += 1
            if (ticks.current >= 80) mostrar()
          }}
          onEngineStop={() => !ajustado.current && mostrar()}
        />
      )}
    </div>
  )
}
