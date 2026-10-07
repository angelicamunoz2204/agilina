from uuid import UUID

from pydantic import Field

from agilina_shared.contract.contract_model import ContractModel
from agilina_shared.contract.participant_context import ParticipantContext
from agilina_shared.enums import Language, OperationMode


class CeremonyContext(ContractModel):
    """What the worker needs to know before joining the room."""

    ceremony_id: UUID
    team_id: UUID
    room: str
    language: Language
    mode: OperationMode
    sprint_day: int = Field(ge=1, description="Current day of the sprint, for the greeting.")
    sprint_total_days: int = Field(ge=1)
    participants: list[ParticipantContext]
    silence_seconds: int = Field(
        default=10, ge=1, description="Threshold X: silence after which Agilina asks."
    )
    stuck_turn_seconds: int = Field(
        default=30, ge=1, description="Threshold Y: stalled turn after which Agilina steps in."
    )
