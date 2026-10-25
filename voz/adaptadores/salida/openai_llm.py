"""Adaptador de salida: GPT-4o mini en Azure OpenAI u OpenAI (implementa ModeloDeLenguaje).

Credenciales en un archivo .env junto a app.py 
    AZURE_OPENAI_CHAT_ENDPOINT='https://<tu-recurso>.openai.azure.com'
    AZURE_OPENAI_CHAT_API_KEY=...
    AZURE_OPENAI_CHAT_DEPLOYMENT='gpt-4o-mini'
    AZURE_OPENAI_CHAT_API_VERSION='2024-12-01-preview'
O bien OpenAI directo:
    OPENAI_API_KEY=sk-...
"""

import logging
import os

from ...dominio.errores import ErrorDelModeloDeLenguaje
from ...dominio.modelos import Mensaje

log = logging.getLogger(__name__)

MODELO = "gpt-4o-mini"


class ModeloOpenAI:
    def __init__(self, modelo: str = MODELO):
        if os.environ.get("AZURE_OPENAI_CHAT_API_KEY"):
            from openai import AzureOpenAI

            # En Azure, "model" es el nombre del deployment.
            self._modelo = os.environ.get("AZURE_OPENAI_CHAT_DEPLOYMENT", modelo)
            self._cliente = AzureOpenAI(
                azure_endpoint=os.environ["AZURE_OPENAI_CHAT_ENDPOINT"],
                api_key=os.environ["AZURE_OPENAI_CHAT_API_KEY"],
                api_version=os.environ.get("AZURE_OPENAI_CHAT_API_VERSION", "2024-12-01-preview"),
            )
            self.descripcion = f"Azure OpenAI (deployment {self._modelo})"
        else:
            from openai import OpenAI

            self._modelo = modelo
            self._cliente = OpenAI()  # toma OPENAI_API_KEY del entorno
            self.descripcion = f"OpenAI ({modelo})"

    def responder(self, instrucciones: str, historial: list[Mensaje], pregunta: str) -> str:
        mensajes = [{"role": "system", "content": instrucciones}]
        mensajes += [{"role": m.rol.value, "content": m.texto} for m in historial]
        mensajes.append({"role": "user", "content": pregunta})
        try:
            r = self._cliente.chat.completions.create(
                model=self._modelo, messages=mensajes, temperature=0.4, max_tokens=400
            )
        except Exception as e:
            raise ErrorDelModeloDeLenguaje(f"GPT falló: {type(e).__name__}: {e}") from e
        return (r.choices[0].message.content or "").strip()


def crear_si_hay_credenciales(modelo: str = MODELO) -> ModeloOpenAI | None:
    """Lee el entorno (ya cargado desde .env) y devuelve el modelo, o None si no hay credenciales."""
    try:
        import openai  # noqa: F401
    except ImportError:
        log.warning("Falta la librería de OpenAI: pip install -r requirements.txt")
        return None
    azure = os.environ.get("AZURE_OPENAI_CHAT_API_KEY")
    if azure and not os.environ.get("AZURE_OPENAI_CHAT_ENDPOINT"):
        log.warning("Hay AZURE_OPENAI_CHAT_API_KEY pero falta AZURE_OPENAI_CHAT_ENDPOINT en el .env.")
        return None
    if not azure and not os.environ.get("OPENAI_API_KEY"):
        log.warning("Sin credenciales en .env: el programa solo repetirá lo que digas (sin GPT).")
        return None
    return ModeloOpenAI(modelo)
