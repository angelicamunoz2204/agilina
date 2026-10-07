from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class GetTeam:
    team_id: UUID
