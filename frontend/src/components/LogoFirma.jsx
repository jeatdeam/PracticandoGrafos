import { useRef } from 'react'
import Lottie from 'lottie-react'
import firma from '../assets/grafoflix.json'

/**
 * Logo "grafoflix" como firma Lottie: se escribe en blanco a mano alzada, letra
 * por letra (fuente Cookie, skill firma-cursiva-lottie), luego un pincelazo rojo
 * la subraya y otros pincelazos dibujan una TV con un botón de play. Se generó
 * en Desktop/lotties-react/firma-grafoflix (trazo_firma.py + agregar_pinceladas.py).
 * Se dibuja una vez al aparecer y se queda quieto; al pasar el cursor se repite.
 * variante: 'nav' (barra superior) o 'grande' (pantallas de inicio y perfiles).
 *   El tamaño es relativo al ancho de la ventana y se define en styles.css
 *   (.logo-firma-nav / .logo-firma-grande); el alto sale de la proporción del Lottie.
 */
export default function LogoFirma({ variante = 'nav' }) {
  const lottie = useRef(null)
  const quieto = typeof window !== 'undefined' && window.matchMedia('(prefers-reduced-motion: reduce)').matches

  const reescribir = () => {
    if (quieto) return
    lottie.current?.goToAndPlay(0, true)
  }

  return (
    <span
      className={`logo-firma logo-firma-${variante}`}
      style={{ aspectRatio: `${firma.w} / ${firma.h}` }}
      onMouseEnter={reescribir}
      aria-hidden="true"
    >
      <Lottie
        lottieRef={lottie}
        animationData={firma}
        loop={false}
        autoplay={!quieto}
        // Quien pidió menos movimiento ve la firma ya escrita (último cuadro)
        onDOMLoaded={() => quieto && lottie.current?.goToAndStop(firma.op - 1, true)}
      />
    </span>
  )
}
