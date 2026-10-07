from uuid import UUID

from pydantic import Field

from agilina_shared.contract.contract_model import ContractModel


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
