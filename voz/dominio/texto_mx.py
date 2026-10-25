"""Reglas de texto para español de México. Funciones puras, fáciles de probar."""

import re

from .modelos import Correccion

_ABREVIATURAS = {
    r"\bCDMX\b": "Ciudad de México",
    r"\bEdomex\b": "Estado de México",
    r"\bLic\.": "licenciado",
    r"\bIng\.": "ingeniero",
    r"\bDr\.": "doctor",
    r"\bDra\.": "doctora",
    r"\bSr\.": "señor",
    r"\bSra\.": "señora",
    r"\bNo\.\s?(?=\d)": "número ",
}


def normalizar_para_voz(texto: str) -> str:
    """Prepara el texto para que la voz lo lea como en México."""
    # "$1,500.50" -> "1500.50 pesos"
    texto = re.sub(
        r"\$\s?([\d,]+(?:\.\d+)?)",
        lambda m: m.group(1).replace(",", "") + " pesos",
        texto,
    )
    # Separadores de miles: "10,000" -> "10000" (la voz lo lee mejor)
    texto = re.sub(r"(?<=\d),(?=\d{3}\b)", "", texto)
    for patron, reemplazo in _ABREVIATURAS.items():
        texto = re.sub(patron, reemplazo, texto)
    return texto


def aplicar_correcciones(texto: str, correcciones: list[Correccion]) -> str:
    """Reemplaza palabras completas, sin importar mayúsculas, conservando la inicial."""
    for c in correcciones:
        patron = re.compile(rf"\b{re.escape(c.incorrecto)}\b", re.IGNORECASE)

        def reemplazo(m: re.Match, bien: str = c.correcto) -> str:
            return bien[:1].upper() + bien[1:] if m.group(0)[:1].isupper() else bien

        texto = patron.sub(reemplazo, texto)
    return texto
