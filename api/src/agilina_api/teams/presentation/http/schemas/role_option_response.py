from pydantic import BaseModel, Field

from agilina_shared.enums import TeamRole


class RoleOptionResponse(BaseModel):
    role: TeamRole
    label: str = Field(
        description=(
            "The code of the label the interface shows for the role; the interface translates "
            "it. Today it is the role itself (`admin` or `member`); HU-04 derives it from the "
            "role and the team's mode."
        )
    )
