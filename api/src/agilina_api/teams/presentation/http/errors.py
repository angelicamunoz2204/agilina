"""The teams errors and the HTTP response each one becomes.

The composition root registers this table in the single handler of
``shared.presentation.http.errors``.
"""

from agilina_api.shared.presentation.http.errors import ErrorMapping
from agilina_api.teams.domain.errors import (
    InvalidTeamNameError,
    LastAdminError,
    MemberNotFoundError,
    RoleChangeDuringActiveSprintError,
    TeamNotFoundError,
)

TEAMS_ERRORS: tuple[ErrorMapping, ...] = (
    ErrorMapping(InvalidTeamNameError, 422, "invalid_team_name"),
    ErrorMapping(TeamNotFoundError, 404, "team_not_found"),
    ErrorMapping(MemberNotFoundError, 404, "member_not_found"),
    ErrorMapping(LastAdminError, 409, "last_admin"),
    ErrorMapping(RoleChangeDuringActiveSprintError, 409, "sprint_in_progress"),
)
