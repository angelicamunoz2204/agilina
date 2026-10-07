from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class RemoveMember:
    team_id: UUID
    user_id: UUID
    """The member who leaves the team (it may be the admin who asks)."""
    requested_by: UUID
    """The admin who asks: the audit log names them."""
