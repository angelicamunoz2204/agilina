"""Port to the identity provider (Keycloak, AD-12): it owns credentials and sessions."""

from typing import Protocol

from agilina_api.identity.domain.value_objects import Email


class IdentityProvider(Protocol):
    async def create_user(self, *, email: Email, full_name: str, password: str) -> str:
        """Create an enabled account with that password and return its subject (the
        ``sub`` claim of its tokens).

        Raises ``PasswordPolicyError`` when the password is refused,
        ``AccountAlreadyExistsError`` when the identity already exists and
        ``IdentityProviderUnavailableError`` when the provider fails.
        """
        ...

    async def delete_user(self, subject: str) -> None:
        """Remove an account: the compensation when the rest of an activation fails."""
        ...
