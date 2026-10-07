from agilina_api.identity.domain.errors.invitation_not_pending_error import (
    InvitationNotPendingError,
)


class InvitationAlreadyUsedError(InvitationNotPendingError):
    """The link was already used."""
