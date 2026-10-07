from agilina_api.shared_kernel import DomainError


class InvitationStillValidError(DomainError):
    """A new invitation was requested but the current link still works."""
