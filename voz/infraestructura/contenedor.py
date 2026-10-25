"""Raíz de composición: el único lugar que conoce todos los adaptadores y los conecta."""

import logging

from ..adaptadores.entrada.web_flask import PreferenciasDePantalla, crear_app
from ..adaptadores.salida import chatterbox_tts, openai_llm
from ..adaptadores.salida.archivos import InstruccionesEnArchivo, VocabularioEnArchivos
from ..adaptadores.salida.memoria import HistorialEnMemoria
from ..adaptadores.salida.piper_tts import SintetizadorPiper
from ..adaptadores.salida.whisper_stt import TranscriptorWhisper
from ..aplicacion.servicios import AsistenteDeVoz
from . import gpu
from .configuracion import Configuracion

log = logging.getLogger(__name__)


def construir(cfg: Configuracion):
    try:
        from dotenv import load_dotenv

        load_dotenv(cfg.dir_datos / ".env")
    except ImportError:
        log.warning("Falta python-dotenv (pip install -r requirements.txt); no leo el archivo .env.")

    gpu.precargar_cuda()
    dispositivo = gpu.elegir_dispositivo(cfg.dispositivo)

    transcriptor = TranscriptorWhisper(cfg.modelo, dispositivo, gpu.liberar_memoria_torch)
    # Chatterbox antes que Piper: al importar PyTorch quedan cargadas sus librerías
    # de CUDA, que también aprovecha onnxruntime-gpu.
    clonadas = chatterbox_tts.crear_si_disponible(cfg.dir_datos / "voces_clonadas", dispositivo, gpu.liberar_memoria_torch)
    piper = SintetizadorPiper(
        usar_cuda=gpu.onnx_puede_usar_gpu(dispositivo, cfg.voz_cpu),
        velocidad=cfg.velocidad,
    )
    modelo = openai_llm.crear_si_hay_credenciales(cfg.modelo_gpt)
    if modelo:
        log.info("Asistente listo: %s, skill %s", modelo.descripcion, cfg.skill.name)

    asistente = AsistenteDeVoz(
        transcriptor=transcriptor,
        sintetizadores=[piper] + ([clonadas] if clonadas else []),
        historial=HistorialEnMemoria(),
        vocabulario=VocabularioEnArchivos(cfg.dir_datos / "vocabulario.txt", cfg.dir_datos / "correcciones.txt"),
        instrucciones=InstruccionesEnArchivo(cfg.skill),
        modelo=modelo,
        voz_por_defecto=cfg.voz,
    )
    return crear_app(asistente, PreferenciasDePantalla(cfg.nombre, cfg.saludo))
