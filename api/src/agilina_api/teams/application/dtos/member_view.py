from dataclasses import dataclass
from uuid import UUID

from agilina_api.teams.domain.member_rules import MemberChangeBlocker
from agilina_shared.enums import TeamRole


@dataclass(frozen=True)
class MemberView:
    """One member of the team as its admin sees it in the team's settings (HU-06)."""

    user_id: UUID
    full_name: str
    email: str
    role: TeamRole
    label: str
    """The code of the visible label of the role, which the interface translates."""
    role_change_blocked_by: MemberChangeBlocker | None
    """Why the member's role cannot change now, or ``None`` when it can."""
    removal_blocked_by: MemberChangeBlocker | None
    """Why the member cannot be removed now, or ``None`` when they can."""
