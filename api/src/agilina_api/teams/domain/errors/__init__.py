"""Errors of the teams domain."""

from agilina_api.teams.domain.errors.already_member_error import AlreadyMemberError
from agilina_api.teams.domain.errors.invalid_team_name_error import InvalidTeamNameError
from agilina_api.teams.domain.errors.last_admin_error import LastAdminError
from agilina_api.teams.domain.errors.member_not_found_error import MemberNotFoundError
from agilina_api.teams.domain.errors.role_change_during_active_sprint_error import (
    RoleChangeDuringActiveSprintError,
)
from agilina_api.teams.domain.errors.team_not_found_error import TeamNotFoundError

__all__ = [
    "AlreadyMemberError",
    "InvalidTeamNameError",
    "LastAdminError",
    "MemberNotFoundError",
    "RoleChangeDuringActiveSprintError",
    "TeamNotFoundError",
]
