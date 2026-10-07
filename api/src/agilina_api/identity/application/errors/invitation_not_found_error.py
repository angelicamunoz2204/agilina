from agilina_api.shared_kernel import DomainError


class InvitationNotFoundError(DomainError):
    """No invitation has that token: the link was altered or never existed."""
