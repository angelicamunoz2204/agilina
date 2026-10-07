from agilina_api.shared_kernel import DomainError


class UnknownTeamError(DomainError):
    """The team an invitation is for does not exist."""
