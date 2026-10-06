"""Data transfer objects of the teams use cases: plain types, no framework."""

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from agilina_api.teams.domain.member_rules import MemberChangeBlocker
from agilina_shared.enums import Language, OperationMode, TeamRole


@dataclass(frozen=True)
class TeamSummary:
    team_id: UUID
    name: str
    language: Language
    admin_user_ids: tuple[UUID, ...]


@dataclass(frozen=True)
class UserTeamView:
    """A team the user is an active member of, with the user's role in it (HU-05)."""

    team_id: UUID
    name: str
    role: TeamRole


@dataclass(frozen=True)
class TeamView:
    """One team as its members see it: its name and how Agilina works in it (HU-05)."""

    team_id: UUID
    name: str
    mode: OperationMode
    language: Language


@dataclass(frozen=True)
class MemberRecord:
    """An active member of a team as stored in teams: who, with which role and since when."""

    user_id: UUID
    role: TeamRole
    joined_at: datetime


@dataclass(frozen=True)
class TeamMemberRecords:
    """A team's active members and whether it has a sprint in progress, read together: what
    the members list needs to tell which changes are blocked and why (HU-06)."""

    members: tuple[MemberRecord, ...]
    has_active_sprint: bool


@dataclass(frozen=True)
class MemberContact:
    """How a member is called and reached. Identity owns it; teams asks for it by port."""

    full_name: str
    email: str


@dataclass(frozen=True)
class RoleOption:
    """A role an admin can give, with the label the interface shows for it."""

    role: TeamRole
    label: str


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


@dataclass(frozen=True)
class TeamMembersList:
    """The team's active members and the roles that can be given to them (HU-06)."""

    roles: tuple[RoleOption, ...]
    members: tuple[MemberView, ...]
