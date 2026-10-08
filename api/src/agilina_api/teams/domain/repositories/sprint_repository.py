from typing import Protocol
from uuid import UUID

from agilina_api.teams.domain.sprint import Sprint


class SprintRepository(Protocol):
    async def add(self, sprint: Sprint) -> None:
        """Store a new sprint with its participants."""
        ...

    async def get_active(self, team_id: UUID) -> Sprint | None:
        """The team's sprint with status ``active``, with its participants in turn order, or
        ``None`` when the team has none."""
        ...

    async def save(self, sprint: Sprint) -> None:
        """Store the changes of a sprint that ``get_active`` loaded, its participants
        included."""
        ...
