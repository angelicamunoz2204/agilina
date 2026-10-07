from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from agilina_api.shared_kernel import DomainError

if TYPE_CHECKING:
    from agilina_api.identity.domain.invitation import InvitationStatus


class InvitationNotPendingError(DomainError):
    """The invitation can no longer be accepted. Subclasses say why."""

    def __init__(self, invitation_id: UUID, state: "InvitationStatus", at: datetime) -> None:
        super().__init__(f"Invitation {invitation_id} is {state.value} at {at.isoformat()}")
        self.invitation_id = invitation_id
        self.state = state
