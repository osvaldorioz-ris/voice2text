"""Adaptadores de salida basados en archivos de texto (implementan Vocabulario e Instrucciones).

Se releen en cada uso: se pueden editar sin reiniciar la aplicación.
"""

from pathlib import Path

from ...dominio.modelos import Correccion


def _lineas(ruta: Path) -> list[str]:
    if not ruta.exists():
        return []
    return [
        l.strip()
        for l in ruta.read_text(encoding="utf-8").splitlines()
        if l.strip() and not l.lstrip().startswith("#")
    ]


class VocabularioEnArchivos:
    def __init__(self, archivo_palabras: Path, archivo_correcciones: Path):
        self._palabras = archivo_palabras
        self._correcciones = archivo_correcciones

    def palabras_clave(self) -> list[str]:
        return _lineas(self._palabras)

    def correcciones(self) -> list[Correccion]:
        reglas = []
        for linea in _lineas(self._correcciones):
            if "=>" in linea:
                mal, bien = (x.strip() for x in linea.split("=>", 1))
                reglas.append(Correccion(mal, bien))
        return reglas


class InstruccionesEnArchivo:
    def __init__(self, archivo: Path):
        self._archivo = archivo

    def leer(self) -> str:
        return self._archivo.read_text(encoding="utf-8")
