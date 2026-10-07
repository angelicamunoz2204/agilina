from dataclasses import dataclass
from uuid import UUID

from agilina_shared.enums import TeamRole


@dataclass(frozen=True)
class AddTeamMember:
    team_id: UUID
    user_id: UUID
    role: TeamRole
