from dataclasses import dataclass
from uuid import UUID

from agilina_shared.enums import TeamRole


@dataclass(frozen=True)
class TeamContext:
    """The team a request is about and the stored membership in it of the user who sent it.

    ``membership_id`` identifies that membership: what the team's records point to when
    they say who did something (an invitation's ``created_by``, HU-06).
    """

    team_id: UUID
    user_id: UUID
    membership_id: UUID
    role: TeamRole
