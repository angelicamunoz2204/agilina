"""Dependency providers declared by the teams presentation layer.

The composition root overrides them with the real handlers, so this layer never imports
the infrastructure one.
"""

from agilina_api.teams.application.commands.create_team_as_admin import CreateTeamAsAdminHandler
from agilina_api.teams.application.queries.get_team import GetTeamHandler
from agilina_api.teams.application.queries.list_my_teams import ListMyTeamsHandler


def get_create_team_as_admin_handler() -> CreateTeamAsAdminHandler:
    raise NotImplementedError("Wired by the composition root")


def get_list_my_teams_handler() -> ListMyTeamsHandler:
    raise NotImplementedError("Wired by the composition root")


def get_get_team_handler() -> GetTeamHandler:
    raise NotImplementedError("Wired by the composition root")
