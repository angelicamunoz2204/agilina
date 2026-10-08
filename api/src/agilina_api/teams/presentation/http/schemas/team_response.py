from uuid import UUID

from pydantic import BaseModel, Field

from agilina_shared.enums import Language, OperationMode, RoleLabel, TeamRole


class TeamResponse(BaseModel):
    id: UUID
    name: str
    mode: OperationMode = Field(
        description=(
            f"How Agilina works in the team. A new team starts in `{OperationMode.SUPPORT}`: "
            "a human Scrum Master approves Agilina's actions."
        )
    )
    language: Language = Field(
        description=f"The team's language, as a code. A new team starts in `{Language.EN}`."
    )
    role: TeamRole = Field(description="The role in the team of the user who asks.")
    label: RoleLabel = Field(
        description=(
            "The code of the label the interface shows for the role, derived from the role and "
            f"the team's mode: `{RoleLabel.SCRUM_MASTER}` for the admin of a team in "
            f"`{OperationMode.SUPPORT}` mode, `{RoleLabel.ADMIN}` in `{OperationMode.AUTONOMOUS}` "
            f"mode, `{RoleLabel.MEMBER}` for a member. It is only shown: permissions follow "
            "`role`."
        )
    )
