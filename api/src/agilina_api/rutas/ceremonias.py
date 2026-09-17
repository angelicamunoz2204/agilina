"""Contrato entre el worker y la API.

Son las dos únicas operaciones que el worker necesita (arquitectura, 5.3):
pedir el contexto antes de entrar a la sala y entregar el resultado al cerrar.
Los tipos ya son definitivos porque viven en el paquete compartido; la
implementación llega con las historias que las persisten (HU-56).
"""

from uuid import UUID

from fastapi import APIRouter, status

from agilina_shared import ContextoCeremonia, ResultadoCeremonia

router = APIRouter(prefix="/v1/ceremonias", tags=["ceremonias"])

PENDIENTE = "Contrato definido en el Sprint 0; implementación pendiente (HU-56)."


@router.get(
    "/{ceremonia_id}/contexto",
    responses={200: {"model": ContextoCeremonia, "description": "Contexto de la ceremonia"}},
    status_code=status.HTTP_501_NOT_IMPLEMENTED,
    summary="Contexto que el worker necesita antes de entrar a la sala",
    description=PENDIENTE,
)
async def obtener_contexto(ceremonia_id: UUID) -> dict[str, str]:
    return {"detalle": PENDIENTE, "ceremonia_id": str(ceremonia_id)}


@router.post(
    "/{ceremonia_id}/resultado",
    status_code=status.HTTP_501_NOT_IMPLEMENTED,
    summary="Resultado que el worker entrega al cerrar la ceremonia",
    description=PENDIENTE,
)
async def entregar_resultado(ceremonia_id: UUID, resultado: ResultadoCeremonia) -> dict[str, str]:
    return {"detalle": PENDIENTE, "ceremonia_id": str(ceremonia_id)}
