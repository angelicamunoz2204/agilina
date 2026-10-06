"""One transaction around a teams command."""

from typing import Protocol

from agilina_api.shared.application.ports import UnitOfWork
from agilina_api.teams.application.ports.outbound.active_sprints import ActiveSprints
from agilina_api.teams.domain.repositories import TeamRepository


class TeamsUnitOfWork(UnitOfWork, Protocol):
    teams: TeamRepository
    sprints: ActiveSprints
    """Read inside the same transaction, after the team is loaded (and locked)."""
