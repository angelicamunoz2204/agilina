"""Read-side port: questions about invitations that do not need the aggregate (CQRS)."""

from datetime import datetime
from typing import Protocol

from agilina_api.identity.application.dtos import InvitationStatusView
from agilina_api.identity.domain.value_objects import TokenHash


class InvitationQueries(Protocol):
    async def get_status(self, token_hash: TokenHash, now: datetime) -> InvitationStatusView | None:
        """What the activation page needs about a link, or ``None`` if no invitation has
        that token (an altered link). The status is the one true at ``now``: a pending
        invitation past its deadline comes back as expired."""
        ...
