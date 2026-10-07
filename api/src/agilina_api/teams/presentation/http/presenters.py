"""Turn application results into response models."""

from uuid import UUID

from agilina_api.teams.application.dtos import (
    ActiveSprintView,
    TeamMembersList,
    TeamView,
    UserTeamView,
)
from agilina_api.teams.presentation.http.schemas import (
    ActiveSprintResponse,
    CreatedTeamResponse,
    DailyParticipantResponse,
    MyTeamResponse,
    RoleOptionResponse,
    SprintDayResponse,
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


def present_active_sprint(view: ActiveSprintView) -> ActiveSprintResponse:
    sprint = view.sprint
    return ActiveSprintResponse(
        id=sprint.sprint_id,
        start_date=sprint.start_date,
        end_date=sprint.end_date,
        daily_time=sprint.daily_time,
        time_zone=sprint.time_zone,
        next_daily_at=view.next_daily_at,
        participants=[
            DailyParticipantResponse(user_id=user_id, turn_order=position)
            for position, user_id in enumerate(sprint.participants, start=1)
        ],
        day=SprintDayResponse(number=view.day.number, total=view.day.total, phase=view.day.phase),
    )
