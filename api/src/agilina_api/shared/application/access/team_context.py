from dataclasses import dataclass
from uuid import UUID

from agilina_shared.enums import TeamRole


@dataclass(frozen=True)
class TeamContext:
    """The team a request is about and the stored role in it of the user who sent it."""

    team_id: UUID
    user_id: UUID
    role: TeamRole
