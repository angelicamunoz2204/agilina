from agilina_api.identity.domain.errors.invitation_not_pending_error import (
    InvitationNotPendingError,
)


class InvitationRevokedError(InvitationNotPendingError):
    """The invitation was cancelled by an admin."""
