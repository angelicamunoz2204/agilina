"""Turn application results into response models."""

from uuid import UUID

from agilina_api.teams.application.dtos import TeamView, UserTeamView
from agilina_api.teams.presentation.http.schemas import (
    CreatedTeamResponse,
    MyTeamResponse,
    TeamResponse,
)
from agilina_shared.enums import TeamRole


def present_created(team_id: UUID) -> CreatedTeamResponse:
    return CreatedTeamResponse(id=team_id)


def present_my_team(view: UserTeamView) -> MyTeamResponse:
    return MyTeamResponse(id=view.team_id, name=view.name, role=view.role)


def present_team(view: TeamView, role: TeamRole) -> TeamResponse:
    return TeamResponse(
        id=view.team_id, name=view.name, mode=view.mode, language=view.language, role=role
    )
