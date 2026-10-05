"""Repository interface of the teams domain."""

from typing import Protocol
from uuid import UUID

from agilina_api.teams.domain.team import Team


class TeamRepository(Protocol):
    async def add(self, team: Team) -> None: ...

    async def get(self, team_id: UUID) -> Team | None:
        """The team with all its memberships, or ``None``."""
        ...

    async def save(self, team: Team) -> None: ...
