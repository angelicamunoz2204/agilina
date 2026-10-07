from uuid import UUID

from pydantic import BaseModel, Field

from agilina_shared.enums import TeamRole


class MyTeamResponse(BaseModel):
    id: UUID
    name: str
    role: TeamRole = Field(description="The user's role in that team.")
