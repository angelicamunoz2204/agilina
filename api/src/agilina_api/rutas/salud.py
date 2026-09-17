"""Sondas de estado.

``/salud`` responde si el proceso está vivo y ``/salud/preparado`` si además
puede atender: es la diferencia entre reiniciar el contenedor y esperar a que
la base de datos vuelva.
"""

from fastapi import APIRouter, Response, status
from pydantic import BaseModel
from sqlalchemy import text

from agilina_api import __version__
from agilina_api.config import obtener_configuracion
from agilina_api.db.sesion import obtener_fabrica_sesiones
from agilina_api.registro import obtener_registro

registro = obtener_registro(__name__)
router = APIRouter(tags=["salud"])


class EstadoServicio(BaseModel):
    servicio: str = "agilina-api"
    version: str
    entorno: str
    estado: str


class EstadoPreparacion(EstadoServicio):
    base_de_datos: str


@router.get("/salud", response_model=EstadoServicio, summary="Sonda de vida")
async def salud() -> EstadoServicio:
    configuracion = obtener_configuracion()
    return EstadoServicio(version=__version__, entorno=configuracion.entorno, estado="vivo")


@router.get(
    "/salud/preparado",
    response_model=EstadoPreparacion,
    summary="Sonda de preparación",
    responses={503: {"description": "Alguna dependencia no responde"}},
)
async def preparado(respuesta: Response) -> EstadoPreparacion:
    configuracion = obtener_configuracion()
    estado_bd = "disponible"
    estado = "preparado"

    try:
        async with obtener_fabrica_sesiones()() as sesion:
            await sesion.execute(text("SELECT 1"))
    except Exception as error:  # noqa: BLE001 - cualquier fallo aquí es indisponibilidad
        registro.warning("La base de datos no responde: %s", error)
        estado_bd = "no disponible"
        estado = "no preparado"
        respuesta.status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    return EstadoPreparacion(
        version=__version__,
        entorno=configuracion.entorno,
        estado=estado,
        base_de_datos=estado_bd,
    )
