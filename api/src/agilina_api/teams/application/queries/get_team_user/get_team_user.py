from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class GetTeamUser:
    team_id: UUID
    user_id: UUID
