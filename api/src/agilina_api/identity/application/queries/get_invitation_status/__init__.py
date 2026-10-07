"""What the activation page needs to know about a link."""

from agilina_api.identity.application.queries.get_invitation_status.get_invitation_status import (
    GetInvitationStatus,
)
from agilina_api.identity.application.queries.get_invitation_status.get_invitation_status_handler import (
    GetInvitationStatusHandler,
)

__all__ = [
    "GetInvitationStatus",
    "GetInvitationStatusHandler",
]
