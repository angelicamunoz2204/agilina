"""Turn application results into response models."""

from uuid import UUID

from agilina_api.teams.application.dtos import TeamMembersList, TeamView, UserTeamView
from agilina_api.teams.presentation.http.schemas import (
    CreatedTeamResponse,
    MyTeamResponse,
    RoleOptionResponse,
    TeamMemberResponse,
    TeamMembersResponse,
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


def present_members(members: TeamMembersList) -> TeamMembersResponse:
    return TeamMembersResponse(
        roles=[
            RoleOptionResponse(role=option.role, label=option.label) for option in members.roles
        ],
        members=[
            TeamMemberResponse(
                user_id=member.user_id,
                full_name=member.full_name,
                email=member.email,
                role=member.role,
                label=member.label,
                role_change_blocked_by=member.role_change_blocked_by,
                removal_blocked_by=member.removal_blocked_by,
            )
            for member in members.members
        ],
    )
