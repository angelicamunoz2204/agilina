"""Domain events of the teams context, named in the past tense."""

from dataclasses import dataclass
from uuid import UUID

from agilina_api.shared_kernel import DomainEvent
from agilina_shared.enums import TeamRole


@dataclass(frozen=True, kw_only=True)
class MemberJoinedTeam(DomainEvent):
    team_id: UUID
    user_id: UUID
    role: TeamRole


@dataclass(frozen=True, kw_only=True)
class MemberRoleChanged(DomainEvent):
    """An admin gave a member another role in the team (HU-06)."""

    team_id: UUID
    user_id: UUID
    previous_role: TeamRole
    role: TeamRole


@dataclass(frozen=True, kw_only=True)
class MemberRemovedFromTeam(DomainEvent):
    """A person stopped being a member of the team (HU-06). Their account is untouched: it
    may belong to other teams."""

    team_id: UUID
    user_id: UUID
    role: TeamRole
