"""One transaction around a teams command."""

from typing import Protocol

from agilina_api.shared.application.ports import UnitOfWork
from agilina_api.teams.domain.repositories import TeamRepository


class TeamsUnitOfWork(UnitOfWork, Protocol):
    teams: TeamRepository
