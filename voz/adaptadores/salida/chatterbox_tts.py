"""Adaptador de salida: voces clonadas con Chatterbox Multilingual (implementa Sintetizador).

"""

import io
import logging
import threading
import time
import wave
from pathlib import Path
from typing import Callable

from ...dominio.errores import ErrorDeSintesis
from ...dominio.modelos import AudioSintetizado

log = logging.getLogger(__name__)

EXTENSIONES = {".wav", ".mp3", ".flac", ".ogg", ".m4a"}


class SintetizadorChatterbox:
    def __init__(self, carpeta: Path, dispositivo: str, liberar_memoria: Callable[[], None] = lambda: None):
        import torch
        from chatterbox.mtl_tts import ChatterboxMultilingualTTS

        if dispositivo == "cuda" and not torch.cuda.is_available():
            log.warning("PyTorch no ve la GPU; las voces clonadas irán en CPU.")
            dispositivo = "cpu"
        log.info("Cargando Chatterbox en %s (la primera vez descarga ~3 GB)...", dispositivo.upper())
        self._dispositivo = dispositivo
        self._liberar_memoria = liberar_memoria if dispositivo == "cuda" else (lambda: None)
        self._modelo = ChatterboxMultilingualTTS.from_pretrained(device=dispositivo)
        self._condiciones = {}
        # El modelo guarda la voz activa en self._modelo.conds; el candado evita
        # que dos peticiones simultáneas mezclen las voces.
        self._candado = threading.Lock()
        for audio in sorted(carpeta.iterdir()):
            if audio.suffix.lower() in EXTENSIONES:
                log.info("Preparando la voz clonada %s (%s)...", audio.stem, audio.name)
                self._modelo.prepare_conditionals(str(audio))
                self._condiciones[audio.stem] = self._modelo.conds

    def voces(self) -> list[str]:
        return list(self._condiciones)

    def sintetizar(self, texto: str, voz: str) -> AudioSintetizado:
        import numpy as np

        try:
            with self._candado:
                inicio = time.perf_counter()
                self._modelo.conds = self._condiciones[voz]
                audio = self._modelo.generate(texto, language_id="es")
                segundos = time.perf_counter() - inicio
                # PyTorch guarda la memoria que usó, pero Whisper no puede tomarla: la devolvemos.
                self._liberar_memoria()
        except Exception as e:
            raise ErrorDeSintesis(f"La voz {voz} falló: {type(e).__name__}: {e}") from e
        duracion = audio.shape[-1] / self._modelo.sr
        log.info("  %s: %.1f s de audio en %.1f s (%s)", voz, duracion, segundos, self._dispositivo.upper())
        muestras = np.clip(audio.squeeze(0).numpy(), -1.0, 1.0)
        buffer = io.BytesIO()
        with wave.open(buffer, "wb") as wav:
            wav.setnchannels(1)
            wav.setsampwidth(2)
            wav.setframerate(self._modelo.sr)
            wav.writeframes((muestras * 32767).astype("<i2").tobytes())
        return AudioSintetizado(buffer.getvalue())


def crear_si_disponible(
    carpeta: Path, dispositivo: str, liberar_memoria: Callable[[], None] = lambda: None
) -> SintetizadorChatterbox | None:
    """Devuelve el sintetizador, o None si no hay audios o falta Chatterbox."""
    if not carpeta.is_dir() or not any(a.suffix.lower() in EXTENSIONES for a in carpeta.iterdir()):
        log.info("Sin voces clonadas: pon audios en %s/ para agregarlas.", carpeta)
        return None
    try:
        import chatterbox  # noqa: F401
    except ImportError:
        log.warning("Hay audios en voces_clonadas/ pero falta Chatterbox: pip install -r requirements-clonacion.txt")
        return None
    try:
        # perth oculta sus errores de importación y deja PerthImplicitWatermarker = None;
        # lo importamos directo para ver la causa real.
        from perth.perth_net.perth_net_implicit.perth_watermarker import (  # noqa: F401
            PerthImplicitWatermarker,
        )
    except ImportError as e:
        log.warning("La marca de agua de Chatterbox no carga (%s).", e)
        if "pkg_resources" in str(e):
            log.warning('Arréglalo con: pip install "setuptools<81"')
        log.warning("Sigo sin voces clonadas.")
        return None
    return SintetizadorChatterbox(carpeta, dispositivo, liberar_memoria)
