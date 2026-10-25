# Asistente de voz (arquitectura hexagonal)

Hablar, Whisper lo pasa a texto, GPT-4o mini (profe de matemáticas) responde y
una voz (Piper o clonada con Chatterbox) lo dice en voz alta.

## Estructura

```
voice2text/
├── app.py                         Punto de entrada (mismas opciones de siempre)
├── voz/
│   ├── dominio/                   Reglas puras, sin librerías externas
│   │   ├── modelos.py             AudioGrabado, AudioSintetizado, Mensaje, Correccion
│   │   ├── errores.py             VozNoEncontrada, ErrorDeTranscripcion, ...
│   │   └── texto_mx.py            "$1,500" -> "1500 pesos", CDMX, correcciones
│   ├── aplicacion/
│   │   ├── puertos.py             Interfaces: Transcriptor, Sintetizador, ModeloDeLenguaje,
│   │   │                          Historial, Vocabulario, Instrucciones
│   │   └── servicios.py           Casos de uso: transcribir, preguntar, hablar, reiniciar
│   ├── adaptadores/
│   │   ├── entrada/
│   │   │   ├── web_flask.py       API HTTP y página (errores del dominio -> códigos HTTP)
│   │   │   └── web/index.html     La interfaz
│   │   └── salida/
│   │       ├── whisper_stt.py     Transcriptor con faster-whisper
│   │       ├── piper_tts.py       Claudia y Daniela (aquí se agregan o quitan voces)
│   │       ├── chatterbox_tts.py  Voces clonadas de voces_clonadas/
│   │       ├── openai_llm.py      GPT-4o mini en Azure u OpenAI (lee el .env)
│   │       ├── archivos.py        vocabulario.txt, correcciones.txt, profesor.md
│   │       └── memoria.py         Historial de la conversación
│   └── infraestructura/
│       ├── configuracion.py       Opciones de línea de comandos
│       ├── gpu.py                 Detección de GPU, CUDA y memoria
│       └── contenedor.py          Conecta adaptadores con casos de uso
├── tests/test_asistente.py        Pruebas con adaptadores falsos (sin GPU ni internet)
├── profesor.md, vocabulario.txt, correcciones.txt, .env, voces_clonadas/
└── requirements.txt, requirements-clonacion.txt
```

La regla: las flechas de dependencia apuntan hacia adentro. `dominio` no importa
nada; `aplicacion` solo importa `dominio`; los adaptadores implementan los puertos;
y solo `infraestructura/contenedor.py` conoce a todos.

## Arrancar

```
source ~/Documentos/python_programs/voice2text/myenv/bin/activate
pip install -r requirements.txt
python app.py --modelo large-v3-turbo --saludo "¡Qué gusto verte de nuevo!"
```

## Probar sin GPU ni modelos

```
python -m unittest discover -s tests -v
```

## Cambiar una pieza

Ejemplo: usar un modelo local en vez de GPT. Crea `voz/adaptadores/salida/ollama_llm.py`
con una clase que tenga `descripcion` y `responder(instrucciones, historial, pregunta)`,
y cámbiala en `infraestructura/contenedor.py`. Los casos de uso y la web no cambian.
