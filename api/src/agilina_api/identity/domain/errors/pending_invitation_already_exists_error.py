from agilina_api.shared_kernel import DomainError


class PendingInvitationAlreadyExistsError(DomainError):
    """There is already a pending invitation for that email in that team."""
