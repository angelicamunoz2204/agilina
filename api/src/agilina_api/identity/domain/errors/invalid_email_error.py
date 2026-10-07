from agilina_api.shared_kernel import DomainError


class InvalidEmailError(DomainError):
    """The text is not a usable email address."""
