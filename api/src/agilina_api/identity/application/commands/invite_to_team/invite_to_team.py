from dataclasses import dataclass
from uuid import UUID

from agilina_shared.enums import TeamRole


@dataclass(frozen=True)
class InviteToTeam:
    team_id: UUID
    inviter_user_id: UUID
    """The admin who invites: always the one behind the access token."""
    inviter_membership_id: UUID
    """The admin's membership in the team: what the invitation records as its author."""
    email: str
    full_name: str
    role: TeamRole = TeamRole.MEMBER
