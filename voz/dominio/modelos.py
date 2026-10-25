"""Objetos del dominio. No dependen de ninguna librería externa."""

from dataclasses import dataclass
from enum import Enum


@dataclass(frozen=True)
class AudioGrabado:
    """Audio que llega del micrófono (normalmente webm del navegador)."""

    contenido: bytes
    extension: str = ".webm"


@dataclass(frozen=True)
class AudioSintetizado:
    """Audio generado por una voz, listo para reproducir."""

    contenido: bytes
    tipo_mime: str = "audio/wav"


class Rol(str, Enum):
    USUARIO = "user"
    ASISTENTE = "assistant"


@dataclass(frozen=True)
class Mensaje:
    rol: Rol
    texto: str


@dataclass(frozen=True)
class Correccion:
    """Regla "lo que escribió el transcriptor => lo correcto"."""

    incorrecto: str
    correcto: str
