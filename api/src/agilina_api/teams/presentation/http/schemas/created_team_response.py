from uuid import UUID

from pydantic import BaseModel


class CreatedTeamResponse(BaseModel):
    id: UUID
