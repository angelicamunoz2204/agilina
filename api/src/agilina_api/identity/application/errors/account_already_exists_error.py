from agilina_api.shared_kernel import DomainError


class AccountAlreadyExistsError(DomainError):
    """The email already has an account (HU-02). Linking it to another team is HU-06."""
