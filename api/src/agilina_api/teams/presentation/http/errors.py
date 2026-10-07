"""The teams errors and the HTTP response each one becomes.

``TeamsErrors`` is the catalog; ``TEAMS_ERRORS`` pairs each domain exception with an entry, and
the composition root registers it in ``shared.presentation.http.error_handlers``. A team that
does not exist answers ``SharedErrors.TEAM_NOT_FOUND``: identity answers it too.
"""

from agilina_api.shared.presentation.http.api_error import ApiError, SharedErrors
from agilina_api.shared.presentation.http.error_handlers import ErrorMapping
from agilina_api.teams.domain.errors import (
    InvalidTeamNameError,
    LastAdminError,
    MemberNotFoundError,
    NoActiveSprintError,
    RoleChangeDuringActiveSprintError,
    TeamNotFoundError,
)


class TeamsErrors:
    INVALID_TEAM_NAME = ApiError(
        422, "invalid_team_name", "The team name is blank or too long once trimmed."
    )
    MEMBER_NOT_FOUND = ApiError(
        404, "member_not_found", "The user is not an active member of the team."
    )
    LAST_ADMIN = ApiError(409, "last_admin", "The team cannot be left without an admin.")
    SPRINT_IN_PROGRESS = ApiError(
        409, "sprint_in_progress", "Roles do not change while a sprint is in progress."
    )
    NO_ACTIVE_SPRINT = ApiError(404, "no_active_sprint", "The team has no active sprint.")


TEAMS_ERRORS: tuple[ErrorMapping, ...] = (
    ErrorMapping(InvalidTeamNameError, TeamsErrors.INVALID_TEAM_NAME),
    ErrorMapping(TeamNotFoundError, SharedErrors.TEAM_NOT_FOUND),
    ErrorMapping(MemberNotFoundError, TeamsErrors.MEMBER_NOT_FOUND),
    ErrorMapping(LastAdminError, TeamsErrors.LAST_ADMIN),
    ErrorMapping(RoleChangeDuringActiveSprintError, TeamsErrors.SPRINT_IN_PROGRESS),
    ErrorMapping(NoActiveSprintError, TeamsErrors.NO_ACTIVE_SPRINT),
)
