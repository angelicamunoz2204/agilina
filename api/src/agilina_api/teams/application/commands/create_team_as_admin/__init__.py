"""A user creates a team and becomes its admin (HU-05)."""

from agilina_api.teams.application.commands.create_team_as_admin.create_team_as_admin import (
    CreateTeamAsAdmin,
)
from agilina_api.teams.application.commands.create_team_as_admin.create_team_as_admin_handler import (
    CreateTeamAsAdminHandler,
)

__all__ = [
    "CreateTeamAsAdmin",
    "CreateTeamAsAdminHandler",
]
