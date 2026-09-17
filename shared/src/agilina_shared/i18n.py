"""Catálogo de textos de Agilina en los dos idiomas del producto.

Toda intervención hablada de Agilina sale de plantillas parametrizadas por
idioma, no del modelo de lenguaje (AD-19). Este módulo es el único lugar donde
viven esos textos, de modo que agregar un idioma sea agregar una columna y no
buscar cadenas por todo el código.
"""

from agilina_shared.enums import Idioma

PLANTILLAS: dict[str, dict[Idioma, str]] = {
    "saludo": {
        Idioma.ES: "Hola, soy Agilina. Estamos en el día {dia} de {total} del sprint. "
        "Empecemos la reunión diaria.",
        Idioma.EN: "Hi, I'm Agilina. We're on day {dia} of {total} of the sprint. "
        "Let's start the daily stand-up.",
    },
    "cede_turno": {
        Idioma.ES: "{nombre}, es tu turno.",
        Idioma.EN: "{nombre}, it's your turn.",
    },
    "silencio": {
        Idioma.ES: "{nombre}, ¿sigues ahí?",
        Idioma.EN: "{nombre}, are you still there?",
    },
    "turno_trabado": {
        Idioma.ES: "{nombre}, ¿quieres cerrar tu turno?",
        Idioma.EN: "{nombre}, would you like to wrap up your turn?",
    },
    "despedida": {
        Idioma.ES: "Con eso cerramos la reunión diaria. Que tengan buen día.",
        Idioma.EN: "That wraps up the daily stand-up. Have a good day.",
    },
    "degradado": {
        Idioma.ES: "No puedo escuchar en este momento: el servicio de transcripción no "
        "responde. Continúen sin mí y yo aviso cuando vuelva.",
        Idioma.EN: "I can't listen right now: the transcription service isn't responding. "
        "Please carry on without me and I'll let you know when I'm back.",
    },
}


def texto(clave: str, idioma: Idioma, **parametros: object) -> str:
    """Devuelve la plantilla ``clave`` en ``idioma`` con sus parámetros resueltos.

    Falla fuerte ante una clave inexistente o un parámetro faltante: un texto a
    medias llegaría a la sala convertido en voz.
    """
    try:
        plantilla = PLANTILLAS[clave][idioma]
    except KeyError as error:
        raise KeyError(f"No existe la plantilla '{clave}' para el idioma '{idioma}'") from error
    return plantilla.format(**parametros)


def claves_incompletas() -> list[str]:
    """Claves que no existen en los dos idiomas.

    La prueba que usa esta función es lo que hace verificable el criterio del
    Definition of Done de que todo texto dirigido al usuario exista en español
    y en inglés.
    """
    return [clave for clave, traducciones in PLANTILLAS.items() if set(traducciones) != set(Idioma)]
