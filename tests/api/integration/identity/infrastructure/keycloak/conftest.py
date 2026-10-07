"""Fixtures of the tests against the real Keycloak (``make test-keycloak``)."""

from collections.abc import AsyncIterator

import pytest

from agilina_api.identity.infrastructure.keycloak.identity_provider import KeycloakIdentityProvider
from agilina_api.shared.infrastructure.settings import get_settings

TENANTS = ("acme", "ecomoda")


@pytest.fixture
def settings():
    return get_settings()


@pytest.fixture(params=TENANTS)
def tenant(request) -> str:
    """Each test that asks for a tenant runs once per tenant: they must behave the same."""
    return str(request.param)


@pytest.fixture
async def provider(settings, tenant) -> AsyncIterator[KeycloakIdentityProvider]:
    provider = KeycloakIdentityProvider(
        base_url=settings.keycloak_url,
        realm=settings.tenant_realm(tenant),
        client_id=settings.keycloak_api_client,
        client_secret=settings.tenant_api_secret(tenant).get_secret_value(),
    )
    yield provider
    await provider._client.aclose()


@pytest.fixture
async def created(provider) -> AsyncIterator[list[str]]:
    """Subjects created by a test, removed afterwards so the realm stays clean."""
    subjects: list[str] = []
    yield subjects
    for subject in subjects:
        await provider.delete_user(subject)
