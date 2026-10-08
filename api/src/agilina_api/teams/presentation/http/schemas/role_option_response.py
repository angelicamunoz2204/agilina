from pydantic import BaseModel, Field

from agilina_shared.enums import RoleLabel, TeamRole


class RoleOptionResponse(BaseModel):
    role: TeamRole
    label: RoleLabel = Field(
        description=(
            "The code of the label the interface shows for the role in this team, derived from "
            "the role and the team's mode; the interface translates it."
        )
    )
