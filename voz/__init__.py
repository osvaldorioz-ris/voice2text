"""Asistente de voz en español de México, organizado en arquitectura hexagonal.

    dominio/          reglas puras del negocio (sin librerías externas)
    aplicacion/       puertos (interfaces) y casos de uso
    adaptadores/      implementaciones concretas de los puertos
        entrada/      quien llama a la aplicación (la web con Flask)
        salida/       a quien llama la aplicación (Whisper, Piper, Chatterbox, GPT, archivos)
    infraestructura/  configuración, GPU y armado de todas las piezas
"""
