"""A Keycloak token becomes the Agilina user it belongs to, against a real PostgreSQL."""

import pytest
from sqlalchemy import text

from agilina_api.identity.infrastructure.keycloak.access_token_verifier import (
    KeycloakAccessTokenVerifier,
)
from agilina_api.identity.infrastructure.keycloak.authenticated_users import (
    KeycloakAuthenticatedUsers,
)
from tests.api.builders import AUDIENCE, ISSUER, AccessTokenBuilder, AppUserBuilder, signing_key
from tests.api.doubles import JWKS_URL, FakeClock, FakeRealmKeys
from tests.api.integration.support import stored_user

pytestmark = pytest.mark.integration


@pytest.fixture
def users(session_factory) -> KeycloakAuthenticatedUsers:
    verifier = KeycloakAccessTokenVerifier(
        jwks_url=JWKS_URL,
        issuer=ISSUER,
        audience=AUDIENCE,
        clock=FakeClock(),
        client=FakeRealmKeys(signing_key()).client(),
    )
    return KeycloakAuthenticatedUsers(verifier, session_factory)


async def test_the_subject_of_a_valid_token_is_resolved_to_its_user(users, session_factory):
    user = await stored_user(
        session_factory, AppUserBuilder().with_unique_email().with_subject("sub-1")
    )
    token = AccessTokenBuilder().for_subject("sub-1").build()

    assert await users.user_id_for(token) == user.id


async def test_a_valid_token_of_someone_agilina_does_not_know_identifies_nobody(
    users, session_factory
):
    await stored_user(session_factory, AppUserBuilder().with_unique_email().with_subject("sub-1"))

    assert await users.user_id_for(AccessTokenBuilder().for_subject("someone-else").build()) is None


async def test_a_user_that_is_not_active_identifies_nobody(users, session_factory, engine):
    await stored_user(session_factory, AppUserBuilder().with_unique_email().with_subject("sub-1"))
    async with engine.begin() as connection:
        await connection.execute(text("UPDATE app_user SET is_active = false"))

    assert await users.user_id_for(AccessTokenBuilder().for_subject("sub-1").build()) is None


async def test_an_invalid_token_does_not_even_reach_the_database():
    verifier = KeycloakAccessTokenVerifier(
        jwks_url=JWKS_URL,
        issuer=ISSUER,
        audience=AUDIENCE,
        clock=FakeClock(),
        client=FakeRealmKeys(signing_key()).client(),
    )
    users = KeycloakAuthenticatedUsers(verifier, session_factory=None)  # type: ignore[arg-type]

    assert await users.user_id_for("not a token") is None
