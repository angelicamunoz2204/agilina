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
