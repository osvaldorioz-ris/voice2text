"""Adaptador de salida: historial de conversación en memoria (implementa Historial)."""

import threading

from ...dominio.modelos import Mensaje


class HistorialEnMemoria:
    def __init__(self):
        self._mensajes: list[Mensaje] = []
        self._candado = threading.Lock()

    def ultimos(self, cantidad: int) -> list[Mensaje]:
        with self._candado:
            return self._mensajes[-cantidad:] if cantidad > 0 else []

    def agregar(self, *mensajes: Mensaje) -> None:
        with self._candado:
            self._mensajes.extend(mensajes)

    def limpiar(self) -> None:
        with self._candado:
            self._mensajes.clear()
