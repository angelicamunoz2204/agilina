from uuid import UUID

from pydantic import BaseModel

from agilina_shared.enums import TeamRole


class ActivatedAccountResponse(BaseModel):
    email: str
    team_id: UUID
    role: TeamRole
