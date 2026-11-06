import { useEffect, useRef, useState } from 'react'
import { api } from './api'
import Setup from './components/Setup'
import ProfileSelect from './components/ProfileSelect'
import Navbar from './components/Navbar'
import Browse from './components/Browse'
import Catalog from './components/Catalog'
import GraphView from './components/GraphView'

export default function App() {
  const [usuarios, setUsuarios] = useState([])
  const [cargado, setCargado] = useState(false)
  const [configurado, setConfigurado] = useState(false)
  const [perfilId, setPerfilId] = useState(null)
  const [vista, setVista] = useState('inicio')
  const [error, setError] = useState(null)
  const [version, setVersion] = useState(0)
  const [aviso, setAviso] = useState(null)
  const temporizador = useRef(null)

  const cargarUsuarios = () =>
    api
      .usuarios()
      .then((lista) => {
        setUsuarios(lista)
        setCargado(true)
      })
      .catch((e) => setError(e.message))

  useEffect(() => {
    cargarUsuarios()
  }, [version])

  const regenerar = async (cantidad) => {
    await api.regenerar(cantidad)
    setPerfilId(null)
    setConfigurado(true)
    setVersion((v) => v + 1)
  }

  const mostrarAviso = (texto) => {
    clearTimeout(temporizador.current)
    setAviso(texto)
    temporizador.current = setTimeout(() => setAviso(null), 4500)
  }

  // Se llama cuando el usuario ve una película: refresca perfiles y avisa si cambió su género
  const alVer = (resultado, pelicula) => {
    if (!resultado.nueva) return
    cargarUsuarios()
    const nuevoGenero = resultado.usuario.genero_favorito
    mostrarAviso(
      nuevoGenero !== resultado.genero_anterior
        ? `Viste «${pelicula.titulo}». Tu género favorito ahora es ${nuevoGenero}: el grafo se actualizó.`
        : `Viste «${pelicula.titulo}». Se agregó a tus películas vistas.`,
    )
  }

  if (error) {
    return (
      <div className="estado">
        <h2>No se pudo conectar con el backend</h2>
        <p>{error}. ¿Está corriendo <code>python -m uvicorn app:app --reload</code> en la carpeta backend?</p>
      </div>
    )
  }

  if (!cargado) return <div className="estado">Cargando...</div>

  if (!configurado) {
    return <Setup guardados={usuarios.length} onGenerar={regenerar} onContinuar={() => setConfigurado(true)} />
  }

  if (perfilId === null) {
    return <ProfileSelect usuarios={usuarios} onElegir={setPerfilId} onConfigurar={() => setConfigurado(false)} />
  }

  const perfil = usuarios.find((u) => u.id === perfilId)

  return (
    <>
      <Navbar
        perfil={perfil}
        usuarios={usuarios}
        vista={vista}
        onVista={setVista}
        onPerfil={setPerfilId}
        onSalir={() => setPerfilId(null)}
      />
      {vista === 'inicio' && (
        <Browse
          key={`${perfilId}-${version}`}
          perfilId={perfilId}
          onPerfil={setPerfilId}
          onVerGrafo={() => setVista('grafo')}
          onExplorar={() => setVista('explorar')}
          onVisto={alVer}
        />
      )}
      {vista === 'explorar' && <Catalog key={`${perfilId}-${version}`} perfilId={perfilId} onVisto={alVer} />}
      {vista === 'grafo' && <GraphView key={`${version}-${perfilId}`} perfilId={perfilId} usuarios={usuarios} />}
      {aviso && <div className="aviso" role="status">{aviso}</div>}
    </>
  )
}
