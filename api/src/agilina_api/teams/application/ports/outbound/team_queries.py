"""Read side of teams (CQRS): questions that need no aggregate."""

from typing import Protocol
from uuid import UUID

from agilina_api.teams.application.dtos import TeamSummary


class TeamQueries(Protocol):
    async def get_summary(self, team_id: UUID) -> TeamSummary | None:
        """The team's name, language and active admins, or ``None`` if it does not exist."""
        ...
