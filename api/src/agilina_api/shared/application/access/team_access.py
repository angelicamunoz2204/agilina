from typing import Protocol
from uuid import UUID

from agilina_shared.enums import TeamRole


class TeamAccess(Protocol):
    """Tells whether a user belongs to a team, against the stored membership.

    Every route about one team checks it before anything else (HU-05): the team is the
    tenant, so the ``team_id`` is part of the signature and cannot be forgotten.
    """

    async def role_of(self, *, team_id: UUID, user_id: UUID) -> TeamRole | None:
        """The user's role in the team while their membership is active; ``None`` when
        they were never a member, were removed, or the team does not exist."""
        ...
