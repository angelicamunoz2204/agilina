"""Punto de entrada del servicio de transcripción.

    make stt   → http://localhost:8001/docs

Solo lo consume el worker, por la red privada de la instancia: este servicio
nunca se expone a internet.
"""

import time

from fastapi import APIRouter, FastAPI, Form, UploadFile
from pydantic import BaseModel

from agilina_shared.enums import Idioma
from agilina_stt import __version__
from agilina_stt.config import obtener_configuracion
from agilina_stt.modelo import obtener_transcriptor

router = APIRouter()


class EstadoServicio(BaseModel):
    servicio: str = "agilina-stt"
    version: str
    estado: str
    modo: str
    modelo: str
    dispositivo: str


class RespuestaTranscripcion(BaseModel):
    texto: str
    idioma: Idioma
    simulada: bool
    duracion_ms: int


@router.get("/salud", response_model=EstadoServicio, tags=["salud"], summary="Sonda de estado")
async def salud() -> EstadoServicio:
    configuracion = obtener_configuracion()
    return EstadoServicio(
        version=__version__,
        estado="vivo",
        modo="simulado" if configuracion.simulado else "modelo",
        modelo=configuracion.modelo,
        dispositivo=configuracion.dispositivo,
    )


@router.post(
    "/v1/transcribir",
    response_model=RespuestaTranscripcion,
    tags=["transcripcion"],
    summary="Transcribe un segmento de audio",
)
async def transcribir(
    audio: UploadFile, idioma: Idioma = Form(default=Idioma.ES)
) -> RespuestaTranscripcion:
    contenido = await audio.read()
    inicio = time.perf_counter()
    resultado = obtener_transcriptor().transcribir(contenido, idioma)
    duracion_ms = int((time.perf_counter() - inicio) * 1000)

    return RespuestaTranscripcion(
        texto=resultado.texto,
        idioma=resultado.idioma,
        simulada=resultado.simulada,
        duracion_ms=duracion_ms,
    )


def crear_aplicacion() -> FastAPI:
    app = FastAPI(
        title="Agilina STT",
        version=__version__,
        description="Transcripción de segmentos de audio. Uso interno del worker.",
    )
    app.include_router(router)
    return app


app = crear_aplicacion()
