"""Keycloak implementation of the ``IdentityProvider`` port.

The API authenticates against Keycloak as its own service account (``agilina-api``,
client credentials) and uses the Admin REST API to create the account of a person who
accepts an invitation. That account can only manage users.
"""

import asyncio
import logging
import time

import httpx

from agilina_api.identity.application.errors import (
    AccountAlreadyExistsError,
    IdentityProviderUnavailableError,
    PasswordPolicyError,
)
from agilina_api.identity.application.ports.outbound import IdentityProvider
from agilina_api.identity.domain.value_objects import Email

logger = logging.getLogger(__name__)

# What Keycloak answers when the password breaks the realm's policy → a stable code.
POLICY_REASONS = {
    "invalidPasswordMinLengthMessage": "min_length",
    "invalidPasswordNotUsernameMessage": "not_username",
    "invalidPasswordNotEmailMessage": "not_email",
}
TOKEN_MARGIN_SECONDS = 30


def split_name(full_name: str) -> tuple[str, str]:
    """Keycloak keeps a first and a last name: the first word and the rest."""
    first, _, rest = full_name.strip().partition(" ")
    return first, rest.strip()


class KeycloakIdentityProvider(IdentityProvider):
    def __init__(  # noqa: PLR0913
        self,
        *,
        base_url: str,
        realm: str,
        client_id: str,
        client_secret: str,
        client: httpx.AsyncClient | None = None,
        timeout: float = 10.0,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._realm = realm
        self._client_id = client_id
        self._client_secret = client_secret
        self._client = client or httpx.AsyncClient(timeout=timeout)
        self._token: str | None = None
        self._token_expires_at = 0.0
        self._token_lock = asyncio.Lock()

    async def aclose(self) -> None:
        await self._client.aclose()

    # ------------------------------------------------------------------- port --
    async def create_user(self, *, email: Email, full_name: str, password: str) -> str:
        first_name, last_name = split_name(full_name)
        payload = {
            "username": email.value,
            "email": email.value,
            "firstName": first_name,
            "lastName": last_name,
            "enabled": True,
            "emailVerified": True,  # the invitation link already proved the address
            "credentials": [{"type": "password", "value": password, "temporary": False}],
        }
        response = await self._admin("POST", "/users", json=payload)

        if response.status_code == httpx.codes.CREATED:
            return self._subject_from(response)
        if response.status_code == httpx.codes.CONFLICT:
            raise AccountAlreadyExistsError("Keycloak already has an account for that email")
        if response.status_code == httpx.codes.BAD_REQUEST:
            reason = self._policy_reason(response)
            if reason is not None:
                raise PasswordPolicyError((reason,))
        raise self._unexpected("create the user", response)

    async def delete_user(self, subject: str) -> None:
        response = await self._admin("DELETE", f"/users/{subject}")
        if response.status_code not in (httpx.codes.NO_CONTENT, httpx.codes.NOT_FOUND):
            raise self._unexpected("delete the user", response)

    # --------------------------------------------------------------- internals --
    async def _admin(self, method: str, path: str, *, json: object = None) -> httpx.Response:
        """One call to the Admin API. A rejected token is renewed once and the call repeated."""
        url = f"{self._base_url}/admin/realms/{self._realm}{path}"
        for attempt in (1, 2):
            token = await self._access_token(force=attempt == 2)
            try:
                response = await self._client.request(
                    method, url, json=json, headers={"Authorization": f"Bearer {token}"}
                )
            except httpx.HTTPError as error:
                raise IdentityProviderUnavailableError(
                    f"Keycloak did not answer ({type(error).__name__})"
                ) from error
            if response.status_code != httpx.codes.UNAUTHORIZED or attempt == 2:
                return response
        raise AssertionError("unreachable")  # pragma: no cover

    async def _access_token(self, *, force: bool = False) -> str:
        async with self._token_lock:
            if not force and self._token and time.monotonic() < self._token_expires_at:
                return self._token
            url = f"{self._base_url}/realms/{self._realm}/protocol/openid-connect/token"
            try:
                response = await self._client.post(
                    url,
                    data={
                        "grant_type": "client_credentials",
                        "client_id": self._client_id,
                        "client_secret": self._client_secret,
                    },
                )
            except httpx.HTTPError as error:
                raise IdentityProviderUnavailableError(
                    f"Keycloak did not answer ({type(error).__name__})"
                ) from error
            if response.status_code != httpx.codes.OK:
                raise self._unexpected("get a token for the API client", response)
            body = response.json()
            self._token = str(body["access_token"])
            lifetime = float(body.get("expires_in", 60))
            self._token_expires_at = time.monotonic() + max(lifetime - TOKEN_MARGIN_SECONDS, 0)
            return self._token

    @staticmethod
    def _subject_from(response: httpx.Response) -> str:
        location: str = response.headers.get("Location", "")
        subject = location.rstrip("/").rsplit("/", 1)[-1]
        if not subject:
            raise IdentityProviderUnavailableError("Keycloak did not say which user it created")
        return subject

    @staticmethod
    def _policy_reason(response: httpx.Response) -> str | None:
        """The password rule that was broken, or ``None`` if the 400 is about something else."""
        try:
            error = str(response.json().get("error", ""))
        except ValueError:
            return None
        if error in POLICY_REASONS:
            return POLICY_REASONS[error]
        return "other" if error.startswith("invalidPassword") else None

    @staticmethod
    def _unexpected(action: str, response: httpx.Response) -> IdentityProviderUnavailableError:
        # Only the status goes in the message: the body can echo what was sent.
        logger.error("Keycloak refused to %s: HTTP %s", action, response.status_code)
        return IdentityProviderUnavailableError(
            f"Keycloak could not {action} (HTTP {response.status_code})"
        )
