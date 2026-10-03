"""Worker ↔ API contract.

These are the only two operations the worker needs (architecture, 5.3):
ask for the context before joining the room and deliver the result on close.
The types are already final because they live in the shared package; the
implementation arrives with the stories that persist them (HU-56).
"""

from uuid import UUID

from fastapi import APIRouter, status

from agilina_shared import CeremonyContext, CeremonyResult

router = APIRouter(prefix="/v1/ceremonies", tags=["ceremonies"])

PENDING = "Contract defined in Sprint 0; implementation pending (HU-56)."


@router.get(
    "/{ceremony_id}/context",
    responses={200: {"model": CeremonyContext, "description": "Ceremony context"}},
    status_code=status.HTTP_501_NOT_IMPLEMENTED,
    summary="Context the worker needs before joining the room",
    description=PENDING,
)
async def get_context(ceremony_id: UUID) -> dict[str, str]:
    return {"detail": PENDING, "ceremony_id": str(ceremony_id)}


@router.post(
    "/{ceremony_id}/result",
    status_code=status.HTTP_501_NOT_IMPLEMENTED,
    summary="Result the worker delivers when the ceremony closes",
    description=PENDING,
)
async def deliver_result(ceremony_id: UUID, result: CeremonyResult) -> dict[str, str]:
    return {"detail": PENDING, "ceremony_id": str(ceremony_id)}
