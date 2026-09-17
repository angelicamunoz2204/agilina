"""Registro de eventos.

La observabilidad mínima que pide la arquitectura es bitácora del planificador
y registro de cada llamada a un adaptador con su resultado. Empieza por una
configuración única para que todos los módulos escriban igual desde el primer
commit.
"""

import logging
import sys


def configurar_registro(nivel: str = "INFO") -> None:
    formato = "%(asctime)s %(levelname)-8s %(name)s · %(message)s"
    logging.basicConfig(
        level=nivel.upper(),
        format=formato,
        datefmt="%Y-%m-%dT%H:%M:%S%z",
        stream=sys.stdout,
        force=True,
    )
    # Uvicorn duplica el acceso con su propio formato; se deja uno solo.
    logging.getLogger("uvicorn.access").propagate = False


def obtener_registro(nombre: str) -> logging.Logger:
    return logging.getLogger(nombre)
