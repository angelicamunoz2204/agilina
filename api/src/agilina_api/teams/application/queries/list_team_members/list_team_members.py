from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class ListTeamMembers:
    team_id: UUID
