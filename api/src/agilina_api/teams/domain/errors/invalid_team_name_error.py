from agilina_api.shared_kernel import DomainError


class InvalidTeamNameError(DomainError):
    """A team's name cannot be blank or longer than 80 characters once trimmed (HU-05)."""
