"""Adaptador de salida: voz a texto con faster-whisper (implementa Transcriptor)."""

import logging
import tempfile
from pathlib import Path
from typing import Callable

from ...dominio.errores import ErrorDeTranscripcion
from ...dominio.modelos import AudioGrabado

log = logging.getLogger(__name__)

# Orienta a Whisper hacia el vocabulario y la ortografía de México.
CONTEXTO_MX = (
    "Transcripción en español de México. Ciudad de México, Guadalajara, Monterrey, "
    "Xochimilco, chamba, ahorita, órale, ¿qué onda?, camión, pesos."
)


class TranscriptorWhisper:
    def __init__(self, modelo: str, dispositivo: str, liberar_memoria: Callable[[], None] = lambda: None):
        from faster_whisper import WhisperModel

        # GPU: int8_float16 (casi la precisión de float16 con la mitad de memoria
        tipo = "int8_float16" if dispositivo == "cuda" else "int8"
        log.info("Cargando el modelo Whisper '%s' en %s (%s)...", modelo, dispositivo.upper(), tipo)
        try:
            self._modelo = WhisperModel(modelo, device=dispositivo, compute_type=tipo)
        except ValueError:
            # GPUs anteriores a la serie RTX 20 no soportan float16 eficiente.
            log.info("GPU no soporta float16; se usa int8.")
            self._modelo = WhisperModel(modelo, device=dispositivo, compute_type="int8")
        self._liberar_memoria = liberar_memoria

    def transcribir(self, audio: AudioGrabado, palabras_clave: list[str]) -> str:
        with tempfile.NamedTemporaryFile(suffix=audio.extension, delete=False) as tmp:
            tmp.write(audio.contenido)
            ruta = Path(tmp.name)
        try:
            try:
                return self._transcribir(ruta, palabras_clave)
            except RuntimeError as e:
                if "out of memory" not in str(e):
                    raise
                log.warning("Memoria de GPU llena al transcribir; se libera memoria y se reintenta...")
                self._liberar_memoria()
                try:
                    return self._transcribir(ruta, palabras_clave)
                except RuntimeError as e2:
                    raise ErrorDeTranscripcion(
                        f"La GPU no tiene memoria suficiente: {e2}. Prueba --modelo medium."
                    ) from e2
        except ErrorDeTranscripcion:
            raise
        except Exception as e:
            raise ErrorDeTranscripcion(f"No se pudo transcribir el audio: {e}") from e
        finally:
            ruta.unlink(missing_ok=True)

    def _transcribir(self, ruta: Path, palabras_clave: list[str]) -> str:
        segmentos, _ = self._modelo.transcribe(
            str(ruta),
            language="es",
            initial_prompt=CONTEXTO_MX,
            hotwords=", ".join(palabras_clave) or None,
            vad_filter=True,  # ignora silencios
            beam_size=5,
            condition_on_previous_text=False,  # evita que un error arrastre al siguiente
        )
        return " ".join(s.text.strip() for s in segmentos).strip()
