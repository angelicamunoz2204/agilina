from typing import Protocol
from uuid import UUID

from agilina_api.identity.domain.invitation import Invitation
from agilina_api.identity.domain.value_objects import Email, TokenHash


class InvitationRepository(Protocol):
    """Every method takes the team, **except** ``get_by_token_hash``: the unguessable
    token is the credential that identifies the invitation, and with it the team, so
    it is the one entry point where the tenant is not known beforehand."""

    async def add(self, invitation: Invitation) -> None:
        """Store a new invitation. Raises ``PendingInvitationAlreadyExistsError`` when the
        team already has a pending one for that email."""
        ...

    async def save(self, invitation: Invitation) -> None: ...

    async def get_by_token_hash(self, token_hash: TokenHash) -> Invitation | None: ...

    async def find_pending(self, team_id: UUID, email: Email) -> Invitation | None: ...
