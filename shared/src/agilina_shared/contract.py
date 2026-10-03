"""Contract between the agent worker and the API.

The worker only needs two operations (architecture document, 5.3):

* get the ceremony context before joining the room;
* deliver the result when the ceremony ends.

Everything that crosses that boundary is here. An incompatible change in these
models breaks the contract between deployables and must be flagged with
``BREAKING CHANGE`` in the commit footer, besides bumping ``CONTRACT_VERSION``.
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from agilina_shared.enums import CeremonyStatus, Language, OperationMode, TeamRole


class ContractModel(BaseModel):
    """Common base: forbids unknown fields so that an incompatibility between
    worker and API fails right away instead of silently."""

    model_config = ConfigDict(extra="forbid", frozen=True)


class ParticipantContext(ContractModel):
    """Who takes part in the ceremony and in which order their turn comes."""

    user_id: UUID
    name: str
    room_identity: str = Field(
        description="Identity the participant uses to join LiveKit; it is the one "
        "the worker uses to attribute what is said."
    )
    role: TeamRole
    turn_order: int = Field(ge=0)


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


class TranscriptSegment(ContractModel):
    """A final transcript fragment attributed to whoever said it.

    The attribution is not computed by acoustic analysis: the identity arrives
    signed in the audio track token.
    """

    user_id: UUID
    room_identity: str
    text: str
    start_ms: int = Field(ge=0)
    end_ms: int = Field(ge=0)


class CeremonyResult(ContractModel):
    """What the worker hands to the API when the ceremony closes.

    No reasoning happens here: the worker delivers the full attributed
    transcript and the API processes it once, outside the latency-critical
    path (AD-19).
    """

    ceremony_id: UUID
    status: CeremonyStatus
    started_at: datetime = Field(description="Always in UTC.")
    closed_at: datetime = Field(description="Always in UTC.")
    present_participants: list[UUID]
    absent_participants: list[UUID] = Field(default_factory=list)
    segments: list[TranscriptSegment]
    degraded: bool = Field(
        default=False,
        description="True when the transcription service did not respond and the "
        "ceremony went on without automatic facilitation.",
    )
    degradation_detail: str | None = None
