#!/usr/bin/env python3
"""Punto de entrada del asistente de voz. Uso igual que antes:

    python app.py --modelo large-v3-turbo --saludo "¡Qué gusto verte de nuevo!"

La estructura del código está explicada en LEEME.md.
"""

import logging
import threading
import webbrowser
from pathlib import Path

from voz.infraestructura.configuracion import leer_configuracion
from voz.infraestructura.contenedor import construir

DIR_APP = Path(__file__).resolve().parent


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    cfg = leer_configuracion(DIR_APP)
    app = construir(cfg)
    url = f"http://localhost:{cfg.puerto}"
    logging.info("Listo: %s", url)
    if not cfg.no_abrir:
        threading.Timer(1.0, webbrowser.open, args=[url]).start()
    app.run(host="127.0.0.1", port=cfg.puerto)


if __name__ == "__main__":
    main()
