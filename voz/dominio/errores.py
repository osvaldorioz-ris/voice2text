"""Errores del dominio. Los adaptadores traducen sus fallas a estos errores
y el adaptador web decide qué código HTTP corresponde a cada uno."""


class ErrorDelAsistente(Exception):
    """Base de todos los errores del asistente."""


class EntradaInvalida(ErrorDelAsistente):
    """Falta texto o audio en la petición."""


class VozNoEncontrada(ErrorDelAsistente):
    def __init__(self, voz: str, disponibles: list[str]):
        super().__init__(f"No conozco la voz '{voz}'. Disponibles: {', '.join(disponibles)}")
        self.voz = voz
        self.disponibles = disponibles


class ErrorDeTranscripcion(ErrorDelAsistente):
    pass


class ErrorDeSintesis(ErrorDelAsistente):
    pass


class ErrorDelModeloDeLenguaje(ErrorDelAsistente):
    pass
