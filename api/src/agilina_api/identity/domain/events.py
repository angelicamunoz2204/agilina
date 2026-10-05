"""Domain events of the identity context, named in the past tense."""

from dataclasses import dataclass
from uuid import UUID

from agilina_api.identity.domain.value_objects import Email
from agilina_api.shared_kernel import DomainEvent
from agilina_shared.enums import TeamRole


@dataclass(frozen=True, kw_only=True)
class InvitationAccepted(DomainEvent):
    """A person activated their account from an invitation link."""

    invitation_id: UUID
    team_id: UUID
    user_id: UUID
    email: Email
    role: TeamRole
