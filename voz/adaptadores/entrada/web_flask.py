"""Adaptador de entrada: la página web y su API HTTP, con Flask.

Traduce peticiones HTTP a llamadas al caso de uso y errores del dominio a códigos HTTP.
"""

import logging
from dataclasses import asdict, dataclass
from pathlib import Path

from flask import Flask, Response, jsonify, request, send_from_directory

from ...aplicacion.servicios import AsistenteDeVoz
from ...dominio.errores import (
    EntradaInvalida,
    ErrorDelAsistente,
    ErrorDelModeloDeLenguaje,
    VozNoEncontrada,
)
from ...dominio.modelos import AudioGrabado

log = logging.getLogger(__name__)
DIR_WEB = Path(__file__).resolve().parent / "web"


@dataclass
class PreferenciasDePantalla:
    nombre: str = "Osvaldo"
    saludo: str = "¡Qué gusto verte, {nombre}!"


def crear_app(asistente: AsistenteDeVoz, pantalla: PreferenciasDePantalla) -> Flask:
    app = Flask(__name__)

    @app.errorhandler(ErrorDelAsistente)
    def _error(e: ErrorDelAsistente):
        if isinstance(e, (EntradaInvalida, VozNoEncontrada)):
            codigo = 400
        elif isinstance(e, ErrorDelModeloDeLenguaje):
            codigo = 502
        else:
            codigo = 500
        if codigo >= 500:
            log.exception("Error atendiendo %s", request.path)
        return jsonify(error=str(e)), codigo

    @app.get("/")
    def inicio():
        return send_from_directory(DIR_WEB, "index.html")

    @app.get("/config")
    def config():
        return jsonify(
            **asdict(pantalla),
            voz=asistente.voz_por_defecto,
            voces=asistente.voces(),
            asistente=asistente.tiene_modelo,
        )

    @app.post("/transcribir")
    def transcribir():
        archivo = request.files.get("audio")
        if archivo is None:
            raise EntradaInvalida("No llegó audio")
        sufijo = Path(archivo.filename or "audio.webm").suffix or ".webm"
        return jsonify(texto=asistente.transcribir(AudioGrabado(archivo.read(), sufijo)))

    @app.post("/preguntar")
    def preguntar():
        datos = request.get_json(silent=True) or {}
        return jsonify(respuesta=asistente.preguntar(datos.get("texto", "")))

    @app.post("/reiniciar")
    def reiniciar():
        asistente.reiniciar()
        return jsonify(ok=True)

    @app.post("/hablar")
    def hablar():
        datos = request.get_json(silent=True) or {}
        audio = asistente.hablar(datos.get("texto", ""), datos.get("voz"))
        return Response(audio.contenido, mimetype=audio.tipo_mime)

    return app
