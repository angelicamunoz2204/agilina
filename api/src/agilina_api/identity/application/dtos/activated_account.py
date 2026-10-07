from dataclasses import dataclass
from uuid import UUID

from agilina_api.identity.domain.value_objects import Email
from agilina_shared.enums import TeamRole


@dataclass(frozen=True)
class ActivatedAccount:
    """The result of activating an account: who, where and with which role."""

    user_id: UUID
    team_id: UUID
    email: Email
    role: TeamRole
