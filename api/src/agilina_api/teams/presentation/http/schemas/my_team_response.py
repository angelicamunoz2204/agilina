from uuid import UUID

from pydantic import BaseModel, Field

from agilina_shared.enums import OperationMode, RoleLabel, TeamRole


class MyTeamResponse(BaseModel):
    id: UUID
    name: str
    role: TeamRole = Field(description="The user's role in that team.")
    mode: OperationMode = Field(description="How Agilina works in that team.")
    label: RoleLabel = Field(
        description=(
            "The code of the label the interface shows for the role, derived from the role and "
            f"the team's mode: `{RoleLabel.SCRUM_MASTER}` for the admin of a team in "
            f"`{OperationMode.SUPPORT}` mode, `{RoleLabel.ADMIN}` in `{OperationMode.AUTONOMOUS}` "
            f"mode, `{RoleLabel.MEMBER}` for a member. It is only shown: permissions follow "
            "`role`."
        )
    )
