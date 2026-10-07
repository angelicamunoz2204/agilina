from dataclasses import dataclass
from uuid import UUID

from agilina_shared.enums import TeamRole


@dataclass(frozen=True)
class ChangeMemberRole:
    team_id: UUID
    user_id: UUID
    """The member whose role changes (it may be the admin who asks)."""
    role: TeamRole
    requested_by: UUID
    """The admin who asks: the audit log names them."""
