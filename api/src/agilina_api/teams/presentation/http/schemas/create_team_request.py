from pydantic import BaseModel, ConfigDict, Field

from agilina_api.teams.domain.team_name import MAX_LENGTH


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
