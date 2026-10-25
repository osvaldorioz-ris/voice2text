"""Adaptador de salida: voces de Piper (implementa Sintetizador)."""

import io
import logging
import wave
from pathlib import Path

from ...dominio.errores import ErrorDeSintesis
from ...dominio.modelos import AudioSintetizado

log = logging.getLogger(__name__)

VOCES_PIPER = {
    "Claudia": "es_MX-claude-high",
    "Daniela": "es_AR-daniela-high"
}
DIR_VOCES = Path.home() / ".cache" / "piper-voces"


class SintetizadorPiper:
    def __init__(
        self,
        voces: dict[str, str] = VOCES_PIPER,
        usar_cuda: bool = False,
        velocidad: float = 1.0,
        dir_voces: Path = DIR_VOCES,
    ):
        from piper import SynthesisConfig

        # length_scale < 1 habla más rápido; velocidad 1.2 = 20 % más rápido.
        self._config = SynthesisConfig(length_scale=1.0 / velocidad)
        self._voces = {}
        for nombre, modelo in voces.items():
            self._voces[nombre] = _cargar(modelo, dir_voces, usar_cuda)
            en_gpu = "CUDAExecutionProvider" in self._voces[nombre].session.get_providers()
            log.info("Voz %s (%s) cargada en %s", nombre, modelo, "GPU" if en_gpu else "CPU")
            if usar_cuda and not en_gpu:
                log.warning("  onnxruntime no pudo usar CUDA; sigue en CPU.")

    def voces(self) -> list[str]:
        return list(self._voces)

    def sintetizar(self, texto: str, voz: str) -> AudioSintetizado:
        try:
            buffer = io.BytesIO()
            wav = wave.open(buffer, "wb")
            self._voces[voz].synthesize_wav(texto, wav, syn_config=self._config)
            wav.close()  # sin "with": si Piper falla, su error no queda tapado por el de close()
        except Exception as e:
            raise ErrorDeSintesis(f"La voz {voz} falló: {type(e).__name__}: {e}") from e
        return AudioSintetizado(buffer.getvalue())


def _cargar(modelo: str, dir_voces: Path, usar_cuda: bool):
    from piper import PiperVoice
    from piper.download_voices import download_voice

    dir_voces.mkdir(parents=True, exist_ok=True)
    ruta = dir_voces / f"{modelo}.onnx"
    if not ruta.exists():
        log.info("Descargando la voz %s (solo la primera vez)...", modelo)
        download_voice(modelo, dir_voces)
    voz = PiperVoice.load(ruta, use_cuda=usar_cuda)
    if usar_cuda:
        # Por defecto onnxruntime reserva memoria de GPU en bloques cada vez más
        # grandes y no la suelta; con Whisper y Chatterbox en la misma tarjeta eso
        # la llena. kSameAsRequested reserva solo lo que cada frase necesita.
        import onnxruntime

        voz.session = onnxruntime.InferenceSession(
            str(ruta),
            sess_options=onnxruntime.SessionOptions(),
            providers=[
                (
                    "CUDAExecutionProvider",
                    {"cudnn_conv_algo_search": "HEURISTIC", "arena_extend_strategy": "kSameAsRequested"},
                ),
                "CPUExecutionProvider",
            ],
        )
    return voz
