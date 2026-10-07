from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from agilina_shared.enums import TeamRole


@dataclass(frozen=True)
class MemberRecord:
    """An active member of a team as stored in teams: who, with which role and since when."""

    user_id: UUID
    role: TeamRole
    joined_at: datetime
