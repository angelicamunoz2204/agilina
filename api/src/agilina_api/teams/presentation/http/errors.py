"""The teams errors and the HTTP response each one becomes.

``TeamsErrors`` is the catalog; ``TEAMS_ERRORS`` pairs each domain exception with an entry, and
the composition root registers it in ``shared.presentation.http.error_handlers``.
"""

from agilina_api.shared.presentation.http.api_error import ApiError
from agilina_api.shared.presentation.http.error_handlers import ErrorMapping
from agilina_api.teams.domain.errors import InvalidTeamNameError, TeamNotFoundError


class TeamsErrors:
    INVALID_TEAM_NAME = ApiError(
        422, "invalid_team_name", "The team name is blank or too long once trimmed."
    )
    TEAM_NOT_FOUND = ApiError(404, "team_not_found", "The team does not exist.")


TEAMS_ERRORS: tuple[ErrorMapping, ...] = (
    ErrorMapping(InvalidTeamNameError, TeamsErrors.INVALID_TEAM_NAME),
    ErrorMapping(TeamNotFoundError, TeamsErrors.TEAM_NOT_FOUND),
)
