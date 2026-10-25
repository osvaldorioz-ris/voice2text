"""
   Adaptador de salida: Gemma 4 local con Ollama (implementa ModeloDeLenguaje).

"""

import json
import logging
import os
import urllib.error
import urllib.request

from ...dominio.errores import ErrorDelModeloDeLenguaje
from ...dominio.modelos import Mensaje

log = logging.getLogger(__name__)

MODELO = "gemma4:e4b"
URL = "http://localhost:11434"


class ModeloOllama:
    def __init__(self, modelo: str = MODELO, url: str | None = None, timeout: float = 120):
        self._modelo = modelo
        self._url = (url or os.environ.get("OLLAMA_HOST") or URL).rstrip("/")
        if not self._url.startswith("http"):
            self._url = "http://" + self._url  # OLLAMA_HOST suele venir como "127.0.0.1:11434"
        self._timeout = timeout
        self.descripcion = f"Ollama ({modelo}) en {self._url}"

    def responder(self, instrucciones: str, historial: list[Mensaje], pregunta: str) -> str:
        mensajes = [{"role": "system", "content": instrucciones}]
        mensajes += [{"role": m.rol.value, "content": m.texto} for m in historial]
        mensajes.append({"role": "user", "content": pregunta})
        datos = self._post(
            "/api/chat",
            {
                "model": self._modelo,
                "messages": mensajes,
                "stream": False,
                "keep_alive": "30m",  # deja el modelo cargado entre preguntas
                "options": {"temperature": 0.4, "num_predict": 400},
            },
        )
        return (datos.get("message", {}).get("content") or "").strip()

    def modelos_instalados(self) -> list[str]:
        return [m.get("name", "") for m in self._get("/api/tags").get("models", [])]

    def _post(self, ruta: str, cuerpo: dict) -> dict:
        peticion = urllib.request.Request(
            self._url + ruta,
            data=json.dumps(cuerpo).encode(),
            headers={"Content-Type": "application/json"},
        )
        return self._enviar(peticion)

    def _get(self, ruta: str) -> dict:
        return self._enviar(urllib.request.Request(self._url + ruta))

    def _enviar(self, peticion: urllib.request.Request) -> dict:
        try:
            with urllib.request.urlopen(peticion, timeout=self._timeout) as r:
                return json.loads(r.read())
        except urllib.error.HTTPError as e:
            detalle = e.read().decode(errors="replace")
            raise ErrorDelModeloDeLenguaje(f"Ollama respondió {e.code}: {detalle}") from e
        except (urllib.error.URLError, TimeoutError, OSError) as e:
            raise ErrorDelModeloDeLenguaje(
                f"No pude hablar con Ollama en {self._url} ({e}). ¿Está corriendo? Prueba: ollama serve"
            ) from e


def crear_si_disponible(modelo: str = MODELO, url: str | None = None) -> ModeloOllama | None:
    """Comprueba que Ollama responde y que el modelo está descargado."""
    ollama = ModeloOllama(modelo, url)
    try:
        instalados = ollama.modelos_instalados()
    except ErrorDelModeloDeLenguaje as e:
        log.warning("%s\nSigo sin modelo de lenguaje (eco).", e)
        return None
    if not any(n == modelo or n == f"{modelo}:latest" for n in instalados):
        log.warning(
            "Ollama no tiene el modelo '%s'. Descárgalo con:\n    ollama pull %s\nSigo sin modelo de lenguaje (eco).",
            modelo,
            modelo,
        )
        return None
    return ollama
