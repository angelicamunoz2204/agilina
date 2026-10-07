from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class ListMyTeams:
    user_id: UUID
