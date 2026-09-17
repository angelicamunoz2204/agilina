"""Enumeraciones del dominio.

Los valores son los que viajan por la API y se guardan en base de datos; las
etiquetas visibles al usuario se resuelven en la capa de presentación, que es
donde vive la regla de que el Administrador se muestra como Scrum Master
cuando el equipo está en modo soporte.
"""

from enum import StrEnum


class ModoOperacion(StrEnum):
    """Lo único que cambia entre los dos modos es si Agilina pide aprobación
    antes de ejecutar una acción."""

    SOPORTE = "soporte"
    AUTONOMO = "autonomo"


class RolEquipo(StrEnum):
    """Roles internos por equipo. Una persona puede ser miembro en un equipo y
    administrador en otro: el rol se resuelve siempre contra el equipo de la
    petición, nunca se toma del token sin contrastarlo con la membresía."""

    ADMINISTRADOR = "administrador"
    MIEMBRO = "miembro"


class Idioma(StrEnum):
    """Atributo del equipo. Parametriza el modelo de transcripción, el juego de
    plantillas, las instrucciones del modelo de lenguaje, la voz sintetizada y
    el idioma del resumen."""

    ES = "es"
    EN = "en"


class TipoCeremonia(StrEnum):
    DAILY = "daily"


class EstadoCeremonia(StrEnum):
    PROGRAMADA = "programada"
    EN_CURSO = "en_curso"
    CERRADA = "cerrada"
    CANCELADA = "cancelada"
    DEGRADADA = "degradada"
