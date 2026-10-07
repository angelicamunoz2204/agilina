from agilina_api.identity.domain.errors.invitation_not_pending_error import (
    InvitationNotPendingError,
)


class InvitationExpiredError(InvitationNotPendingError):
    """The link expired (seven days after it was issued)."""
