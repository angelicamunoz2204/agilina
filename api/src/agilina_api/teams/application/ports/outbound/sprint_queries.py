"""Read side of the sprint (CQRS): the team's active sprint, with no aggregate."""

from typing import Protocol
from uuid import UUID

from agilina_api.teams.application.dtos import ActiveSprintRecord


class SprintQueries(Protocol):
    async def active_sprint_of(self, team_id: UUID) -> ActiveSprintRecord | None:
        """The team's sprint with status ``active``, with its participants in turn order, or
        ``None`` when the team has none (or does not exist)."""
        ...
