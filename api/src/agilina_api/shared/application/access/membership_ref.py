from dataclasses import dataclass
from uuid import UUID

from agilina_shared.enums import TeamRole


@dataclass(frozen=True)
class MembershipRef:
    """A user's stored, active membership in one team: which one it is and its role."""

    membership_id: UUID
    role: TeamRole
