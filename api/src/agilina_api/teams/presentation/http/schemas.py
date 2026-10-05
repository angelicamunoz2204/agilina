"""Request and response models of the teams API."""

from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from agilina_api.teams.domain.team_name import MAX_LENGTH
from agilina_shared.enums import Language, OperationMode, TeamRole


class CreateTeamRequest(BaseModel):
    """Only the name: whoever creates the team comes from the access token, and every new
    team starts with the same mode and language."""

    # An unknown field (``created_by``, ``mode``…) is refused, not silently ignored.
    model_config = ConfigDict(extra="forbid")

    name: str = Field(
        description=(
            "The team's name. Surrounding spaces are trimmed; a blank name, or one longer "
            f"than {MAX_LENGTH} characters once trimmed, answers `422 invalid_team_name`. "
            "Names may repeat: a team is identified by its id."
        ),
        examples=["Atlas"],
    )


class CreatedTeamResponse(BaseModel):
    id: UUID


class MyTeamResponse(BaseModel):
    id: UUID
    name: str
    role: TeamRole = Field(description="The user's role in that team.")


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
