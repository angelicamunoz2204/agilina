from uuid import UUID

from pydantic import BaseModel, Field

from agilina_shared.enums import Language, OperationMode, TeamRole


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
