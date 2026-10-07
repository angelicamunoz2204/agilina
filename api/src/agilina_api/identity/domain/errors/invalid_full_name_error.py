from agilina_api.shared_kernel import DomainError


class InvalidFullNameError(DomainError):
    """A person's name cannot be blank."""
