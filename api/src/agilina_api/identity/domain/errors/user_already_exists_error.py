from agilina_api.shared_kernel import DomainError


class UserAlreadyExistsError(DomainError):
    """There is already an account with that email or that Keycloak identity (HU-02)."""
