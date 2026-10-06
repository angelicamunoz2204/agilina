"""Port to the teams context: put a person into a team."""

from typing import Protocol
from uuid import UUID

from agilina_shared.enums import TeamRole


class TeamMembership(Protocol):
    """Identity cannot import teams (AD-21), so it asks for this through a port that the
    composition root implements with the teams use case. It works inside the caller's
    transaction: it never commits."""

    async def add_member(self, *, team_id: UUID, user_id: UUID, role: TeamRole) -> None:
        """Put the user into the team with ``role``; someone who had been removed comes
        back. Raises ``AlreadyTeamMemberError`` when they are an active member and
        ``UnknownTeamError`` when the team does not exist."""
        ...
