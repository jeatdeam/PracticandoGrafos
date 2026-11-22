import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import ForceGraph3D from 'react-force-graph-3d'
import * as THREE from 'three'
import SpriteText from 'three-spritetext'
import { colorAvatar, colorGenero } from '../colores'

/**
 * Grafo de usuarios en 3D (three.js).
 * Cada nodo es una esfera formada por bolitas repartidas de forma pareja sobre
 * su superficie (espiral de Fibonacci), que gira y "late" suavemente.
 * - Género: esfera grande con el nombre del género en el centro.
 * - Usuarios: esferas pequeñas con el color de su avatar y su nombre debajo.
 * - Usuario destacado: esfera blanca algo más grande.
 * areaIzq / areaDer: fracción del ancho (0 a 1) libre a la izquierda/derecha.
 * areaArriba / areaAbajo: fracción del alto (0 a 1) libre arriba/abajo.
 * alinear: 'centro' (en la zona libre) o 'derecha' (pegado al borde derecho).
 * escala: agranda el grafo (1.25 = 25% más grande).
 * reinicio: número que, al cambiar, devuelve la cámara a la vista inicial.
 * enfocarGenero: nombre de un género para agrandar su figura ('' = ninguna).
 * interactivo: permite zoom con la rueda y mover la vista (pestaña de grafos).
 * recorrido: { miembros: Set(ids), visitados: Map(id -> orden), actual: id, arbol: Set("a-b") }
 *   para mostrar paso a paso un BFS/DFS sobre los usuarios recorridos
 *   (miembros). Con él, un clic en un usuario llama directamente a
 *   onNodeClick (nodo inicial).
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

// Esfera de bolitas: puntos parejos sobre la superficie (espiral de Fibonacci)
// brillo: mezcla aditiva (las bolitas se suman y brillan, efecto neón);
// sin brillo se ven con su color normal
function esferaDeBolitas(cantidad, radio, color, tamano, brillo = false) {
  const posiciones = new Float32Array(cantidad * 3)
  const anguloDorado = Math.PI * (3 - Math.sqrt(5))
  for (let i = 0; i < cantidad; i++) {
    const r = radio * (0.97 + Math.random() * 0.03)
    const phi = Math.acos(1 - (2 * (i + 0.5)) / cantidad)
    const theta = i * anguloDorado
    posiciones[i * 3] = r * Math.sin(phi) * Math.cos(theta)
    posiciones[i * 3 + 1] = r * Math.cos(phi)
    posiciones[i * 3 + 2] = r * Math.sin(phi) * Math.sin(theta)
  }
  const geometria = new THREE.BufferGeometry()
  geometria.setAttribute('position', new THREE.BufferAttribute(posiciones, 3))
  const material = new THREE.PointsMaterial({
    size: tamano,
    map: bolita(),
    color,
    transparent: true,
    depthWrite: false,
    blending: brillo ? THREE.AdditiveBlending : THREE.NormalBlending,
  })
  const puntos = new THREE.Points(geometria, material)
  // Cada esfera gira y late con su propio ritmo
  puntos.userData.fase = Math.random() * Math.PI * 2
  puntos.userData.velocidad = (0.2 + Math.random() * 0.25) * (Math.random() < 0.5 ? -1 : 1)
  return puntos
}

// Solo el núcleo (género) es un poco neón: su color de la leyenda, algo más
// saturado y claro, y con brillo. Los usuarios usan colores normales.
function neonSuave(hex) {
  const c = new THREE.Color(hex)
  const hsl = {}
  c.getHSL(hsl)
  c.setHSL(hsl.h, Math.min(1, hsl.s * 1.2 + 0.1), Math.min(0.62, hsl.l + 0.08))
  return `#${c.getHexString()}`
}

// Arista del árbol BFS/DFS dibujada como una fila de puntos de color neón
const PUNTOS_ARISTA = 48
const COLOR_ARBOL = '#00f0ff'
function aristaPunteada() {
  const geometria = new THREE.BufferGeometry()
  geometria.setAttribute('position', new THREE.BufferAttribute(new Float32Array(PUNTOS_ARISTA * 3), 3))
  const puntos = new THREE.Points(geometria, new THREE.PointsMaterial({
    size: 0.9,
    map: bolita(),
    color: COLOR_ARBOL,
    transparent: true,
    depthWrite: false,
    blending: THREE.AdditiveBlending,
  }))
  puntos.frustumCulled = false
  puntos.userData.punteada = true
  return puntos
}
// Reparte los puntos a lo largo de la arista (la librería llama esto en
// cada cuadro); devuelve false para las aristas normales
function moverArista(obj, { start, end }) {
  if (!obj?.userData?.punteada) return false
  const arr = obj.geometry.attributes.position.array
  for (let i = 0; i < PUNTOS_ARISTA; i++) {
    const f = (i + 0.5) / PUNTOS_ARISTA
    arr[i * 3] = start.x + (end.x - start.x) * f
    arr[i * 3 + 1] = start.y + (end.y - start.y) * f
    arr[i * 3 + 2] = start.z + (end.z - start.z) * f
  }
  obj.geometry.attributes.position.needsUpdate = true
  return true
}

// "#rrggbb" + alfa -> "rgba(...)" (la librería usa el alfa como opacidad)
function conAlfa(hex, alfa) {
  const c = new THREE.Color(hex)
  return `rgba(${Math.round(c.r * 255)},${Math.round(c.g * 255)},${Math.round(c.b * 255)},${alfa})`
}

// Colores de un nodo según el recorrido BFS/DFS: los usuarios recorridos
// (miembros) sin visitar en gris, visitados con su color y su número de
// orden, el actual en amarillo. Los nodos de género (agrupadores visuales)
// quedan tenues; los demás nodos conservan sus colores normales.
function pintarRecorrido(n, rec) {
  const material = n.__nube?.material
  if (!material) return
  let color = n.__colorBase
  let opacidad = 1
  let etiqueta = n.__nombre
  if (rec && n.tipo === 'usuario' && rec.miembros.has(n.id)) {
    const orden = rec.visitados.get(n.id)
    if (n.id === rec.actual) color = '#ffd23f'
    else if (orden === undefined) { color = '#5a5a5a'; opacidad = 0.45 }
    if (orden !== undefined) etiqueta = `${orden}. ${n.__nombre}`
  } else if (rec && n.tipo === 'genero') {
    opacidad = 0.35
  }
  material.color.set(color)
  material.opacity = opacidad
  if (n.__etiqueta && n.__etiqueta.text !== etiqueta) n.__etiqueta.text = etiqueta
}

// Giro y latido de la esfera entera: barato aunque haya cientos de nodos
function animarNube(puntos, t) {
  const { fase, velocidad } = puntos.userData
  puntos.rotation.y = fase + t * velocidad
  puntos.rotation.x = 0.4 * Math.sin(t * 0.3 + fase)
  puntos.scale.setScalar(1 + 0.03 * Math.sin(t * 1.3 + fase))
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
// Cuánto crecen las nubes de la figura enfocada
const ESCALA_FOCO = 1.3

export default function Grafo3D({ datos, destacadoId, onNodeClick, areaIzq = 0, areaDer = 0, areaArriba = 0, areaAbajo = 0, alinear = 'centro', escala = 1, interactivo = false, recorrido = null, reinicio = 0, enfocarGenero = '' }) {
  const contenedor = useRef(null)
  const grafo = useRef(null)
  const ajustado = useRef(false)
  const ticks = useRef(0)
  // Nodo enfocado (al hacer clic): se ve grande al centro y los demás pequeños
  const enfocado = useRef(null)
  // Distancia de cámara del encuadre general y si la cámara está en transición
  const distanciaGeneral = useRef(null)
  const transicion = useRef(false)
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

  // El bucle de animación lee el recorrido actual desde aquí
  const recorridoRef = useRef(recorrido)
  recorridoRef.current = recorrido

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
    enfocado.current = null
    transicion.current = false
    setListo(false)
  }, [datosGrafo, montado, moverse])

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
    distanciaGeneral.current = distancia
    // Con un nodo enfocado, la cámara la maneja el bucle de abajo
    if (enfocado.current) return
    if (ms > 0) {
      transicion.current = true
      return
    }
    const p = camara.position
    const largo = Math.hypot(p.x, p.y, p.z) || 1
    grafo.current.cameraPosition(
      { x: (p.x / largo) * distancia, y: (p.y / largo) * distancia, z: (p.z / largo) * distancia },
      { x: 0, y: 0, z: 0 },
      ms,
    )
  }

  // Distancia para que el nodo enfocado ocupe ~40% de la zona libre
  // Distancia para que la figura enfocada (su género y sus usuarios, ya
  // agrandados) llene el lienzo: queda más grande que en la vista general
  const distanciaFoco = (genero) => {
    const camara = grafo.current.camera()
    const tanV = Math.tan((camara.fov * Math.PI) / 360)
    const miembros = datosGrafo.nodes.filter((n) => n.genero === genero.genero)
    const radio = Math.max(20, ...miembros.map((n) => Math.hypot((n.x ?? 0) - (genero.x ?? 0), (n.y ?? 0) - (genero.y ?? 0), (n.z ?? 0) - (genero.z ?? 0))))
    // Al agrandar solo crecen las esferas (x1.3), no las distancias entre
    // nodos: se suma el radio de la esfera agrandada y el nombre de debajo
    const radioFigura = radio + 4.5 * ESCALA_FOCO + 5
    // La figura ocupa ~92% del alto del contenedor
    return radioFigura / (tanV * 0.92)
  }

  // Bucle propio (independiente del motor de fuerzas, así nada se congela):
  // - mueve las bolitas dentro de cada nube
  // - agranda el nodo enfocado y achica los demás de forma suave
  // - lleva la cámara hacia el nodo enfocado y lo sigue mientras flota
  useEffect(() => {
    if (!montado) return
    let cuadro
    const destino = new THREE.Vector3()
    const animar = () => {
      cuadro = requestAnimationFrame(animar)
      const g = grafo.current
      if (!g) return
      if (moverse) {
        const t = performance.now() / 1000
        datosGrafo.nodes.forEach((n) => n.__nube && animarNube(n.__nube, t))
      }
      const foco = enfocado.current
      datosGrafo.nodes.forEach((n) => {
        if (!n.__grupo) return
        const rec = recorridoRef.current
        const meta = rec
          ? n.tipo === 'genero' ? 1
            : !rec.miembros.has(n.id) ? 0.5 : n.id === rec.actual ? 1.8 : rec.visitados.has(n.id) ? 1.1 : 0.85
          : foco ? (n.genero === foco.genero ? ESCALA_FOCO : 0.5) : 1
        const actual = n.__grupo.scale.x
        if (Math.abs(meta - actual) > 0.001) n.__grupo.scale.setScalar(actual + (meta - actual) * 0.1)
      })
      if (!foco && !transicion.current) return
      const camara = g.camera()
      const controles = g.controls()
      // El centro de giro va hacia el nodo (o al origen al salir) y la cámara
      // se traslada con él
      destino.set(foco ? foco.x ?? 0 : 0, foco ? foco.y ?? 0 : 0, foco ? foco.z ?? 0 : 0)
      const antes = controles.target.clone()
      controles.target.lerp(destino, 0.08)
      camara.position.add(controles.target.clone().sub(antes))
      if (transicion.current) {
        const meta = foco ? distanciaFoco(foco) : distanciaGeneral.current
        const dir = camara.position.clone().sub(controles.target)
        const largo = dir.length() || 1
        const nuevo = largo + (meta - largo) * 0.08
        camara.position.copy(controles.target).add(dir.multiplyScalar(nuevo / largo))
        if (Math.abs(meta - nuevo) < 0.5 && controles.target.distanceTo(destino) < 0.5) transicion.current = false
      }
    }
    cuadro = requestAnimationFrame(animar)
    return () => cancelAnimationFrame(cuadro)
  }, [datosGrafo, moverse, montado, tamano, areaIzq, areaDer, areaArriba, areaAbajo])

  // La "figura" de un nodo es su género con todos sus usuarios
  const generoDe = (n) =>
    n.tipo === 'genero' ? n : datosGrafo.nodes.find((g) => g.tipo === 'genero' && g.genero === n.genero)

  const enfocar = (genero) => {
    if (!genero || enfocado.current === genero) return
    enfocado.current = genero
    transicion.current = true
  }
  const desenfocar = () => {
    if (!enfocado.current) return
    enfocado.current = null
    transicion.current = true
  }

  // Figura que contiene un punto de la pantalla: el clic cae dentro del
  // círculo que forman en pantalla su género y sus usuarios (borde incluido)
  const figuraEn = (evento) => {
    const g = grafo.current
    if (!g || !evento) return null
    const caja = contenedor.current.getBoundingClientRect()
    const x = evento.clientX - caja.left
    const y = evento.clientY - caja.top
    let mejor = null
    datosGrafo.nodes.filter((n) => n.tipo === 'genero').forEach((genero) => {
      const centro = g.graph2ScreenCoords(genero.x ?? 0, genero.y ?? 0, genero.z ?? 0)
      const radio = Math.max(40, ...datosGrafo.nodes
        .filter((n) => n.genero === genero.genero)
        .map((n) => {
          const p = g.graph2ScreenCoords(n.x ?? 0, n.y ?? 0, n.z ?? 0)
          return Math.hypot(p.x - centro.x, p.y - centro.y)
        })) + 30
      const d = Math.hypot(x - centro.x, y - centro.y)
      if (d <= radio && (!mejor || d < mejor.d)) mejor = { genero, d }
    })
    return mejor?.genero ?? null
  }

  // Clic en un nodo: si su figura no está agrandada, se agranda. Si ya lo
  // está, un usuario lleva a su perfil / sub-grafo (acción de siempre).
  const alClicNodo = (n) => {
    const genero = generoDe(n)
    if (enfocado.current && enfocado.current === genero) {
      if (n.tipo === 'usuario') onNodeClick?.(Number(n.id))
      return
    }
    enfocar(genero)
  }

  // Clic en una línea o en un hueco: si cae dentro de una figura, se agranda
  // esa figura; con una figura agrandada, un clic fuera de ella la devuelve
  const alClicFuera = (evento) => {
    const figura = figuraEn(evento)
    if (enfocado.current) {
      if (figura && figura !== enfocado.current) enfocar(figura)
      else if (!figura) desenfocar()
      return
    }
    enfocar(figura)
  }

  // Elegir un género en la lista agranda su figura; "Todos" vuelve a la vista general
  useEffect(() => {
    if (!listo) return
    if (enfocarGenero) enfocar(datosGrafo.nodes.find((n) => n.tipo === 'genero' && n.genero === enfocarGenero))
    else desenfocar()
  }, [enfocarGenero, listo])

  // Botón "Restablecer vista": quita el enfoque y vuelve al encuadre inicial
  // (sirve también si la rueda dejó la cámara muy cerca o muy lejos)
  useEffect(() => {
    if (!reinicio || !ajustado.current) return
    enfocado.current = null
    encuadrar(800)
  }, [reinicio])

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
    const color = esGenero ? neonSuave(colorGenero(n.genero)) : esDestacado ? '#ffffff' : colorAvatar(Number(n.id))
    const grupo = new THREE.Group()

    // El núcleo (género) es mucho más denso que los usuarios para distinguirlo
    const cantidad = esGenero ? 5000 : esDestacado ? 1100 : 900
    const puntos = esferaDeBolitas(cantidad, radio, color, esGenero ? 0.6 : 0.45, esGenero)
    grupo.add(puntos)
    n.__nube = puntos
    n.__grupo = grupo
    n.__colorBase = color

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
      n.__etiqueta = nombre
      n.__nombre = n.label.replace(/-\d+$/, '')
    }
    pintarRecorrido(n, recorridoRef.current)
    return grupo
  }, [destacadoId])

  // Al avanzar el recorrido se repintan los nodos (sin recrearlos)
  useEffect(() => {
    datosGrafo.nodes.forEach((n) => pintarRecorrido(n, recorrido))
  }, [recorrido, datosGrafo])

  // Las aristas llevan su transparencia en el color; las del árbol del
  // recorrido (padre -> hijo) se dibujan como una fila de puntos neón
  const extremo = (x) => (typeof x === 'object' ? x.id : x)
  const enArbol = (l) => recorrido?.arbol.has(`${extremo(l.source)}-${extremo(l.target)}`) ||
    recorrido?.arbol.has(`${extremo(l.target)}-${extremo(l.source)}`)
  const colorArista = useCallback((l) => {
    if (recorrido) {
      if (enArbol(l)) return 'rgba(0,240,255,0.25)'
      return l.tipo === 'genero' ? 'rgba(255,255,255,0.04)' : 'rgba(255,255,255,0.1)'
    }
    if (l.tipo !== 'genero') return 'rgba(255,255,255,0.16)'
    return conAlfa(colorPorNodo.get(extremo(l.target)) ?? colorPorNodo.get(extremo(l.source)) ?? '#ffffff', 0.16)
  }, [colorPorNodo, recorrido])
  const objetoArista = useCallback((l) => (recorrido && enArbol(l) ? aristaPunteada() : null), [recorrido])

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
          linkOpacity={1}
          linkWidth={0}
          linkThreeObject={objetoArista}
          linkThreeObjectExtend
          linkPositionUpdate={moverArista}
          onNodeClick={(n) => (recorrido ? n.tipo === 'usuario' && onNodeClick?.(Number(n.id)) : alClicNodo(n))}
          onLinkClick={(_, evento) => !recorrido && alClicFuera(evento)}
          onBackgroundClick={(evento) => !recorrido && alClicFuera(evento)}
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
