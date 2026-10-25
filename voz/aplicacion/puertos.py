"""Puertos: lo que la aplicación necesita del mundo exterior, sin decir cómo.

"""

from typing import Protocol

from ..dominio.modelos import AudioGrabado, AudioSintetizado, Correccion, Mensaje


class Transcriptor(Protocol):
    """Voz a texto."""

    def transcribir(self, audio: AudioGrabado, palabras_clave: list[str]) -> str: ...


class Sintetizador(Protocol):
    """Texto a voz. Un sintetizador puede ofrecer varias voces."""

    def voces(self) -> list[str]: ...

    def sintetizar(self, texto: str, voz: str) -> AudioSintetizado: ...


class ModeloDeLenguaje(Protocol):
    """Genera la respuesta del asistente."""

    descripcion: str

    def responder(self, instrucciones: str, historial: list[Mensaje], pregunta: str) -> str: ...


class Historial(Protocol):
    """Memoria de la conversación."""

    def ultimos(self, cantidad: int) -> list[Mensaje]: ...

    def agregar(self, *mensajes: Mensaje) -> None: ...

    def limpiar(self) -> None: ...


class Vocabulario(Protocol):
    """Palabras que el transcriptor debe preferir y correcciones posteriores."""

    def palabras_clave(self) -> list[str]: ...

    def correcciones(self) -> list[Correccion]: ...


class Instrucciones(Protocol):
    """El "skill" del asistente (por ejemplo, profesor de matemáticas)."""

    def leer(self) -> str: ...
