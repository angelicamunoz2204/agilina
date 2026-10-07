from dataclasses import dataclass
from datetime import datetime

from agilina_api.identity.domain.invitation import InvitationStatus
from agilina_shared.enums import TeamRole


@dataclass(frozen=True)
class InvitationStatusView:
    """What the activation page shows about a link (HU-02)."""

    email: str
    full_name: str
    role: TeamRole
    status: InvitationStatus
    expires_at: datetime
