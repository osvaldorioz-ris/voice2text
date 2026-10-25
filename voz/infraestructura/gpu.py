"""Detección de GPU NVIDIA y manejo de sus librerías (detalle técnico, fuera del dominio)."""

import ctypes
import glob
import logging
import sys
from pathlib import Path

log = logging.getLogger(__name__)


def precargar_cuda() -> None:
    """Carga cuBLAS y cuDNN instalados con pip (paquetes nvidia-*-cu12), sin LD_LIBRARY_PATH."""
    try:
        import nvidia  # paquete "namespace" de nvidia-cublas-cu12 / nvidia-cudnn-cu12
    except ImportError:
        return
    for base in nvidia.__path__:
        for patron in ("cublas/lib/libcublasLt.so.*", "cublas/lib/libcublas.so.*", "cudnn/lib/libcudnn*.so.*"):
            for lib in sorted(glob.glob(str(Path(base) / patron))):
                try:
                    ctypes.CDLL(lib, mode=ctypes.RTLD_GLOBAL)
                except OSError:
                    pass


def _cublas_disponible() -> bool:
    try:
        ctypes.CDLL("libcublas.so.12", mode=ctypes.RTLD_GLOBAL)
        return True
    except OSError:
        return False


def elegir_dispositivo(pedido: str) -> str:
    """'auto' usa la GPU si existe y tiene sus librerías; si no, la CPU."""
    if pedido == "cpu":
        return "cpu"
    import ctranslate2

    if ctranslate2.get_cuda_device_count() == 0:
        if pedido == "cuda":
            sys.exit("Pediste --dispositivo cuda pero no veo ninguna GPU NVIDIA (revisa nvidia-smi).")
        return "cpu"
    # La GPU se detecta aunque falten las librerías de CUDA; avisamos desde el inicio.
    if sys.platform.startswith("linux") and not _cublas_disponible():
        aviso = (
            "Hay GPU pero falta cuBLAS/cuDNN en este entorno. Instálalos con:\n"
            '    pip install nvidia-cublas-cu12 "nvidia-cudnn-cu12==9.*"'
        )
        if pedido == "cuda":
            sys.exit(aviso)
        log.warning(aviso + "\nMientras tanto uso CPU.")
        return "cpu"
    return "cuda"


def onnx_puede_usar_gpu(dispositivo: str, forzar_cpu: bool) -> bool:
    """Piper usa la GPU si hay CUDA y está instalado onnxruntime-gpu compatible."""
    if forzar_cpu or dispositivo != "cuda":
        return False
    import onnxruntime

    if "CUDAExecutionProvider" not in onnxruntime.get_available_providers():
        log.warning(
            "Las voces de Piper irán en CPU: falta onnxruntime-gpu. Para usar la GPU:\n"
            '    pip uninstall -y onnxruntime onnxruntime-gpu && pip install "onnxruntime-gpu==1.26.*"\n'
            "(1.26 es la última versión para CUDA 12; las nuevas piden CUDA 13)"
        )
        return False
    try:
        onnxruntime.preload_dlls()
    except Exception:
        pass
    return True


def liberar_memoria_torch() -> None:
    """Devuelve a la GPU la memoria que PyTorch tiene guardada, para que Whisper la pueda usar."""
    if "torch" in sys.modules:
        import torch

        if torch.cuda.is_available():
            torch.cuda.empty_cache()
