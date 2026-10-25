"""Casos de uso del asistente de voz. Solo hablan con puertos."""

import logging
import threading

from ..dominio.errores import EntradaInvalida, VozNoEncontrada
from ..dominio.modelos import AudioGrabado, AudioSintetizado, Mensaje, Rol
from ..dominio.texto_mx import aplicar_correcciones, normalizar_para_voz
from .puertos import Historial, Instrucciones, ModeloDeLenguaje, Sintetizador, Transcriptor, Vocabulario

log = logging.getLogger(__name__)


class AsistenteDeVoz:
    def __init__(
        self,
        transcriptor: Transcriptor,
        sintetizadores: list[Sintetizador],
        historial: Historial,
        vocabulario: Vocabulario,
        instrucciones: Instrucciones,
        modelo: ModeloDeLenguaje | None = None,
        voz_por_defecto: str | None = None,
        max_turnos: int = 10,
    ):
        self._transcriptor = transcriptor
        self._historial = historial
        self._vocabulario = vocabulario
        self._instrucciones = instrucciones
        self._modelo = modelo
        self._max_turnos = max_turnos
        self._candado = threading.Lock()
        # Catálogo nombre de voz -> sintetizador que la ofrece (la primera gana).
        self._catalogo: dict[str, Sintetizador] = {}
        for s in sintetizadores:
            for v in s.voces():
                self._catalogo.setdefault(v, s)
        if not self._catalogo:
            raise ValueError("Se necesita al menos una voz")
        if voz_por_defecto not in self._catalogo:
            if voz_por_defecto:
                log.warning("La voz '%s' no existe; uso %s.", voz_por_defecto, self.voces()[0])
            voz_por_defecto = self.voces()[0]
        self.voz_por_defecto = voz_por_defecto

    # --- consultas -------------------------------------------------------
    def voces(self) -> list[str]:
        return list(self._catalogo)

    @property
    def tiene_modelo(self) -> bool:
        return self._modelo is not None

    # --- casos de uso ----------------------------------------------------
    def transcribir(self, audio: AudioGrabado) -> str:
        if not audio.contenido:
            raise EntradaInvalida("No llegó audio")
        texto = self._transcriptor.transcribir(audio, self._vocabulario.palabras_clave())
        return aplicar_correcciones(texto, self._vocabulario.correcciones())

    def preguntar(self, pregunta: str) -> str:
        pregunta = pregunta.strip()
        if not pregunta:
            raise EntradaInvalida("No hay pregunta")
        if self._modelo is None:
            return pregunta  # sin modelo de lenguaje: eco
        with self._candado:
            respuesta = self._modelo.responder(
                self._instrucciones.leer(),
                self._historial.ultimos(2 * self._max_turnos),
                pregunta,
            )
            self._historial.agregar(Mensaje(Rol.USUARIO, pregunta), Mensaje(Rol.ASISTENTE, respuesta))
        log.info("Tú: %s | Asistente: %s", pregunta, respuesta)
        return respuesta

    def hablar(self, texto: str, voz: str | None = None) -> AudioSintetizado:
        texto = texto.strip()
        if not texto:
            raise EntradaInvalida("No hay texto para leer")
        voz = voz or self.voz_por_defecto
        sintetizador = self._catalogo.get(voz)
        if sintetizador is None:
            raise VozNoEncontrada(voz, self.voces())
        log.info("Hablando con la voz %s", voz)
        return sintetizador.sintetizar(normalizar_para_voz(texto), voz)

    def reiniciar(self) -> None:
        self._historial.limpiar()
