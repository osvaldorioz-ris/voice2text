"""Pruebas de los casos de uso y de la API web con adaptadores falsos.

No necesitan GPU, modelos ni internet:
    python -m unittest discover -s tests -v
"""

import io
import unittest

from voz.adaptadores.entrada.web_flask import PreferenciasDePantalla, crear_app
from voz.adaptadores.salida.memoria import HistorialEnMemoria
from voz.aplicacion.servicios import AsistenteDeVoz
from voz.dominio.errores import EntradaInvalida, ErrorDelModeloDeLenguaje, VozNoEncontrada
from voz.dominio.modelos import AudioGrabado, AudioSintetizado, Correccion


class TranscriptorFalso:
    def __init__(self, texto):
        self.texto, self.palabras = texto, None

    def transcribir(self, audio, palabras_clave):
        self.palabras = palabras_clave
        return self.texto


class SintetizadorFalso:
    def __init__(self, *voces):
        self._voces, self.pedidos = list(voces), []

    def voces(self):
        return self._voces

    def sintetizar(self, texto, voz):
        self.pedidos.append((texto, voz))
        return AudioSintetizado(f"{voz}:{texto}".encode())


class ModeloFalso:
    descripcion = "falso"

    def __init__(self, falla=False):
        self.llamadas, self.falla = [], falla

    def responder(self, instrucciones, historial, pregunta):
        if self.falla:
            raise ErrorDelModeloDeLenguaje("sin conexión")
        self.llamadas.append((instrucciones, [m.texto for m in historial], pregunta))
        return f"respuesta {len(self.llamadas)}"


class VocabularioFalso:
    def palabras_clave(self):
        return ["gatitos", "Kiwi"]

    def correcciones(self):
        return [Correccion("latitos", "gatitos")]


class InstruccionesFalsas:
    def leer(self):
        return "Eres el profe"


def armar(modelo=None, voz=None):
    piper, clonadas = SintetizadorFalso("Claudia", "Daniela"), SintetizadorFalso("Andres")
    stt = TranscriptorFalso("Tengo tres latitos")
    asistente = AsistenteDeVoz(
        stt, [piper, clonadas], HistorialEnMemoria(), VocabularioFalso(), InstruccionesFalsas(), modelo, voz, max_turnos=1
    )
    return asistente, stt, piper, clonadas


class CasosDeUso(unittest.TestCase):
    def test_transcribir_usa_vocabulario_y_correcciones(self):
        a, stt, *_ = armar()
        self.assertEqual(a.transcribir(AudioGrabado(b"x")), "Tengo tres gatitos")
        self.assertEqual(stt.palabras, ["gatitos", "Kiwi"])

    def test_sin_modelo_hace_eco(self):
        a, *_ = armar()
        self.assertEqual(a.preguntar(" hola "), "hola")

    def test_preguntar_envia_instrucciones_e_historial_limitado(self):
        m = ModeloFalso()
        a, *_ = armar(m)
        a.preguntar("uno")
        a.preguntar("dos")
        a.preguntar("tres")
        self.assertEqual(m.llamadas[0], ("Eres el profe", [], "uno"))
        # max_turnos=1: solo el último par pregunta/respuesta
        self.assertEqual(m.llamadas[2][1], ["dos", "respuesta 2"])

    def test_reiniciar_borra_historial(self):
        m = ModeloFalso()
        a, *_ = armar(m)
        a.preguntar("uno")
        a.reiniciar()
        a.preguntar("dos")
        self.assertEqual(m.llamadas[1][1], [])

    def test_hablar_normaliza_y_elige_sintetizador(self):
        a, _, piper, clonadas = armar()
        a.hablar("Cuesta $1,500 en la CDMX", "Andres")
        a.hablar("Hola")
        self.assertEqual(clonadas.pedidos, [("Cuesta 1500 pesos en la Ciudad de México", "Andres")])
        self.assertEqual(piper.pedidos, [("Hola", "Claudia")])

    def test_voz_inexistente(self):
        a, *_ = armar()
        with self.assertRaises(VozNoEncontrada):
            a.hablar("hola", "Aldo")

    def test_voz_por_defecto_invalida_usa_la_primera(self):
        a, *_ = armar(voz="Aldo")
        self.assertEqual(a.voz_por_defecto, "Claudia")

    def test_entradas_vacias(self):
        a, *_ = armar()
        for llamada in (lambda: a.preguntar(" "), lambda: a.hablar(""), lambda: a.transcribir(AudioGrabado(b""))):
            with self.assertRaises(EntradaInvalida):
                llamada()


class ApiWeb(unittest.TestCase):
    def setUp(self):
        self.asistente, *_ = armar(ModeloFalso())
        self.web = crear_app(self.asistente, PreferenciasDePantalla("Osvaldo", "¡Hola!")).test_client()

    def test_config(self):
        c = self.web.get("/config").json
        self.assertEqual((c["voces"], c["voz"], c["saludo"], c["asistente"]), (["Claudia", "Daniela", "Andres"], "Claudia", "¡Hola!", True))

    def test_flujo_completo(self):
        texto = self.web.post("/transcribir", data={"audio": (io.BytesIO(b"x"), "a.webm")}).json["texto"]
        respuesta = self.web.post("/preguntar", json={"texto": texto}).json["respuesta"]
        audio = self.web.post("/hablar", json={"texto": respuesta, "voz": "Daniela"})
        self.assertEqual((texto, respuesta, audio.data, audio.mimetype), ("Tengo tres gatitos", "respuesta 1", b"Daniela:respuesta 1", "audio/wav"))

    def test_errores_se_traducen_a_http(self):
        self.assertEqual(self.web.post("/hablar", json={"texto": "x", "voz": "Aldo"}).status_code, 400)
        self.assertEqual(self.web.post("/preguntar", json={}).status_code, 400)
        self.assertEqual(self.web.post("/transcribir").status_code, 400)
        a, *_ = armar(ModeloFalso(falla=True))
        web = crear_app(a, PreferenciasDePantalla()).test_client()
        r = web.post("/preguntar", json={"texto": "hola"})
        self.assertEqual((r.status_code, r.json["error"]), (502, "sin conexión"))


if __name__ == "__main__":
    unittest.main()
