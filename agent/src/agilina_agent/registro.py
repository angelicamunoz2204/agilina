"""Registro del worker, con el mismo formato que el de la API."""

import logging
import sys


def configurar_registro(nivel: str = "INFO") -> None:
    logging.basicConfig(
        level=nivel.upper(),
        format="%(asctime)s %(levelname)-8s %(name)s · %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S%z",
        stream=sys.stdout,
        force=True,
    )


def obtener_registro(nombre: str) -> logging.Logger:
    return logging.getLogger(nombre)
