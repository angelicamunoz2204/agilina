"""Punto de entrada de la API.

Levantar: ``make api`` · Documentación interactiva: http://localhost:8000/docs
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from agilina_api import __version__
from agilina_api.config import obtener_configuracion
from agilina_api.planificador import crear_planificador
from agilina_api.registro import configurar_registro, obtener_registro
from agilina_api.rutas import ceremonias, salud

registro = obtener_registro(__name__)

DESCRIPCION = """
Fuente de verdad del dominio de Agilina.

Esta especificación es el contrato con la aplicación web y con el worker del
agente: se genera a partir de los tipos, de modo que no puede quedar
desalineada del código.
"""


@asynccontextmanager
async def ciclo_de_vida(app: FastAPI):
    """Arranca el planificador con la aplicación y lo detiene con ella.

    Si la base de datos no está disponible, la API sigue arriba sin
    planificador y lo registra: un trabajo diferido no debe tumbar la API.
    """
    configuracion = obtener_configuracion()
    configurar_registro(configuracion.nivel_log)
    registro.info("Iniciando agilina-api %s en entorno %s", __version__, configuracion.entorno)

    planificador = None
    try:
        planificador = crear_planificador()
        planificador.start()
        app.state.planificador = planificador
        registro.info("Planificador iniciado")
    except Exception as error:  # noqa: BLE001 - seguir sin planificador es degradación, no caída
        app.state.planificador = None
        registro.warning("El planificador no pudo iniciarse: %s", error)

    yield

    if planificador is not None and planificador.running:
        planificador.shutdown(wait=False)
        registro.info("Planificador detenido")


def crear_aplicacion() -> FastAPI:
    configuracion = obtener_configuracion()
    app = FastAPI(
        title="Agilina API",
        version=__version__,
        description=DESCRIPCION,
        lifespan=ciclo_de_vida,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=configuracion.origenes,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(salud.router)
    app.include_router(ceremonias.router)
    return app


app = crear_aplicacion()
