"""Opciones de línea de comandos (las mismas de antes)."""

import argparse
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Configuracion:
    modelo: str
    dispositivo: str
    voz_cpu: bool
    nombre: str
    voz: str | None
    saludo: str
    modelo_gpt: str
    skill: Path
    velocidad: float
    puerto: int
    no_abrir: bool
    dir_datos: Path


def leer_configuracion(dir_datos: Path, argv: list[str] | None = None) -> Configuracion:
    p = argparse.ArgumentParser(description="Asistente de voz en español de México")
    p.add_argument("--modelo", default="small", help="Whisper: tiny, base, small, medium, large-v3-turbo o large-v3")
    p.add_argument("--dispositivo", default="auto", choices=["auto", "cuda", "cpu"], help="auto usa la GPU si la encuentra")
    p.add_argument("--voz-cpu", action="store_true", help="Forzar las voces de Piper en CPU aunque haya GPU")
    p.add_argument("--nombre", default="Osvaldo", help="Nombre para el saludo")
    p.add_argument("--voz", default=None, help="Voz inicial: Claudia, Daniela o el nombre de una voz clonada")
    p.add_argument("--saludo", default="¡Qué gusto verte, {nombre}!", help="{nombre} se reemplaza por --nombre")
    p.add_argument("--modelo-gpt", default="gpt-4o-mini", help="Modelo de OpenAI (en Azure manda el deployment del .env)")
    p.add_argument("--skill", type=Path, default=dir_datos / "profesor.md", help="Instrucciones del asistente")
    p.add_argument("--velocidad", type=float, default=1.0, help="Velocidad de las voces de Piper")
    p.add_argument("--puerto", type=int, default=5000)
    p.add_argument("--no-abrir", action="store_true", help="No abrir el navegador")
    a = p.parse_args(argv)
    return Configuracion(
        modelo=a.modelo,
        dispositivo=a.dispositivo,
        voz_cpu=a.voz_cpu,
        nombre=a.nombre,
        voz=a.voz,
        saludo=a.saludo,
        modelo_gpt=a.modelo_gpt,
        skill=a.skill,
        velocidad=a.velocidad,
        puerto=a.puerto,
        no_abrir=a.no_abrir,
        dir_datos=dir_datos,
    )
