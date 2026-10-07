"""The Keycloak adapter against the real Keycloak with the ``agilina`` realm imported.

Run with ``make test-keycloak``. They check what the simulated tests assume: that the
realm gives the API's service account the right to manage users, that its password policy
answers with the codes the adapter reads, and that a refused password leaves no user behind.
"""

import uuid

import httpx
import pytest

from agilina_api.identity.application.errors import (
    AccountAlreadyExistsError,
    IdentityProviderUnavailableError,
    PasswordPolicyError,
)
from agilina_api.identity.domain.value_objects import Email
from agilina_api.identity.infrastructure.keycloak.identity_provider import KeycloakIdentityProvider

pytestmark = pytest.mark.keycloak

PASSWORD = "a-very-long-password-1"  # noqa: S105 - a test value


def _email() -> Email:
    return Email(f"it-{uuid.uuid4().hex[:10]}@example.test")


async def _find(provider: KeycloakIdentityProvider, email: Email) -> list[dict]:
    token = await provider._access_token()
    url = f"{provider._base_url}/admin/realms/{provider._realm}/users"
    async with httpx.AsyncClient() as client:
        response = await client.get(
            url,
            params={"email": email.value, "exact": "true"},
            headers={"Authorization": f"Bearer {token}"},
        )
    assert response.status_code == 200
    return response.json()


async def test_a_valid_account_is_created_enabled_and_verified(provider, created):
    email = _email()

    subject = await provider.create_user(email=email, full_name="Julián Torres", password=PASSWORD)
    created.append(subject)

    [user] = await _find(provider, email)
    assert user["id"] == subject  # the Location header is the `sub` of its tokens
    assert user["enabled"] is True and user["emailVerified"] is True
    assert user["username"] == email.value
    assert (user["firstName"], user["lastName"]) == ("Julián", "Torres")


async def test_a_password_below_the_minimum_length_is_refused_and_leaves_no_user(provider):
    email = _email()

    with pytest.raises(PasswordPolicyError) as raised:
        await provider.create_user(email=email, full_name="Julián Torres", password="short")

    assert raised.value.reasons == ("min_length",)
    assert await _find(provider, email) == []


async def test_a_password_equal_to_the_email_is_refused(provider):
    email = _email()

    with pytest.raises(PasswordPolicyError) as raised:
        await provider.create_user(email=email, full_name="Julián Torres", password=email.value)

    assert raised.value.reasons == ("not_username",)
    assert await _find(provider, email) == []


async def test_an_email_that_already_has_an_account_is_reported(provider, created):
    email = _email()
    created.append(
        await provider.create_user(email=email, full_name="Julián Torres", password=PASSWORD)
    )

    with pytest.raises(AccountAlreadyExistsError):
        await provider.create_user(email=email, full_name="Julián Torres", password=PASSWORD)


async def test_a_deleted_account_is_gone_and_deleting_it_again_is_harmless(provider):
    email = _email()
    subject = await provider.create_user(email=email, full_name="Julián Torres", password=PASSWORD)

    await provider.delete_user(subject)
    await provider.delete_user(subject)

    assert await _find(provider, email) == []


async def test_a_name_without_a_last_name_is_accepted(provider, created):
    created.append(await provider.create_user(email=_email(), full_name="Cher", password=PASSWORD))


async def test_a_wrong_client_secret_is_an_outage_not_a_crash(settings, tenant):
    provider = KeycloakIdentityProvider(
        base_url=settings.keycloak_url,
        realm=settings.tenant_realm(tenant),
        client_id=settings.keycloak_api_client,
        client_secret="not-the-secret",  # noqa: S106
    )

    with pytest.raises(IdentityProviderUnavailableError, match="401"):
        await provider.create_user(email=_email(), full_name="Julián Torres", password=PASSWORD)
    await provider._client.aclose()
