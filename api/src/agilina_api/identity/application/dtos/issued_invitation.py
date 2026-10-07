from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True)
class IssuedInvitation:
    """The result of issuing an invitation. It never carries the token: that travels only
    in the email."""

    invitation_id: UUID
    expires_at: datetime
