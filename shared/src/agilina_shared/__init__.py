"""Modelos de dominio y contrato compartidos por los desplegables de Agilina.

Este paquete es la razón de que Agilina viva en un solo repositorio: el contrato
entre el worker y la API se expresa como tipos compartidos y no como
documentación que se desactualiza (documento de arquitectura, sección 5.2).
"""

from agilina_shared.contrato import (
    ContextoCeremonia,
    ParticipanteContexto,
    ResultadoCeremonia,
    SegmentoTranscripcion,
)
from agilina_shared.enums import (
    EstadoCeremonia,
    Idioma,
    ModoOperacion,
    RolEquipo,
    TipoCeremonia,
)

__all__ = [
    "ContextoCeremonia",
    "EstadoCeremonia",
    "Idioma",
    "ModoOperacion",
    "ParticipanteContexto",
    "ResultadoCeremonia",
    "RolEquipo",
    "SegmentoTranscripcion",
    "TipoCeremonia",
    "VERSION_CONTRATO",
]

VERSION_CONTRATO = "1.0"
"""Versión del contrato worker ↔ API.

Cambiarla es un BREAKING CHANGE y debe declararse en el pie del commit
(documento de Avance 1, sección 7.3).
"""
