"""Outbound ports: what the teams use cases need from the outside world."""

from agilina_api.teams.application.ports.outbound.team_queries import TeamQueries
from agilina_api.teams.application.ports.outbound.teams_unit_of_work import TeamsUnitOfWork

__all__ = ["TeamQueries", "TeamsUnitOfWork"]
