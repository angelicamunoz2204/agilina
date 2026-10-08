"""Port: whether a team has a sprint in progress (HU-06)."""

from typing import Protocol
from uuid import UUID


class ActiveSprints(Protocol):
    """The one question «does the team have an active sprint?». The role change (inside its
    transaction) and the members list ask it through this port, and the read of the active
    sprint answers with the same predicate, so it is answered in a single place."""

    async def has_active_sprint(self, team_id: UUID) -> bool:
        """Whether the team has a sprint with status ``active``."""
        ...
