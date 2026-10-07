from dataclasses import dataclass
from uuid import UUID

from agilina_shared.enums import Language, TeamRole


@dataclass(frozen=True)
class IssueInvitation:
    team_id: UUID
    team_name: str
    email: str
    full_name: str
    role: TeamRole
    language: Language
    """The language of the email: the team's."""
    created_by: UUID | None = None
    """The member who issues it, or ``None`` when the platform operator does (AD-22)."""
    inviter_name: str | None = None
