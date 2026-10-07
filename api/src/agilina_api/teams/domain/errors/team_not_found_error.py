from agilina_api.shared_kernel import DomainError


class TeamNotFoundError(DomainError):
    """There is no team with that identifier."""
