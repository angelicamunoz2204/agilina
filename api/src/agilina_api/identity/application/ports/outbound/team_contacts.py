"""Port to the teams context: who to tell about a team."""

from typing import Protocol
from uuid import UUID

from agilina_api.identity.application.dtos import TeamContacts


class TeamContactsDirectory(Protocol):
    async def get(self, team_id: UUID) -> TeamContacts | None:
        """The team's name, language and admins' contacts, or ``None`` if it does not exist."""
        ...
