from agilina_api.shared_kernel import DomainError


class InvalidActivationTokenError(DomainError):
    """The text does not have the shape of an activation token (an altered link)."""
