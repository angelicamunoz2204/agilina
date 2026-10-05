"""The Keycloak adapter against a simulated Keycloak (``httpx.MockTransport``).

It checks what the adapter sends and how it reads every answer. That the answers are the
ones the real Keycloak gives is checked in the mirrored folder of ``tests/api/integration``
(make test-keycloak).
"""

import json

import httpx
import pytest

from agilina_api.identity.application.errors import (
    AccountAlreadyExistsError,
    IdentityProviderUnavailableError,
    PasswordPolicyError,
)
from agilina_api.identity.domain.value_objects import Email
from agilina_api.identity.infrastructure.keycloak.identity_provider import (
    KeycloakIdentityProvider,
    split_name,
)

USER_ID = "a5b30f20-929f-413f-a767-c328958e9a65"
PASSWORD = "a-very-long-password-1"


class FakeKeycloak:
    """Answers like Keycloak and remembers what it was asked."""

    def __init__(self) -> None:
        self.requests: list[httpx.Request] = []
        self.token_calls = 0
        self.create_status = 201
        self.create_body: dict[str, object] = {}
        self.delete_status = 204
        self.reject_next_tokens = 0  # answers 401 to this many admin calls, as an expired token
        self.token_status = 200
        self.expires_in = 900

    def handler(self, request: httpx.Request) -> httpx.Response:
        self.requests.append(request)
        if request.url.path.endswith("/protocol/openid-connect/token"):
            self.token_calls += 1
            if self.token_status != 200:
                return httpx.Response(self.token_status, json={"error": "unauthorized_client"})
            return httpx.Response(
                200,
                json={"access_token": f"token-{self.token_calls}", "expires_in": self.expires_in},
            )
        if self.reject_next_tokens > 0:
            self.reject_next_tokens -= 1
            return httpx.Response(401)
        if request.method == "POST" and request.url.path.endswith("/users"):
            headers = {"Location": f"http://kc/admin/realms/agilina/users/{USER_ID}"}
            return httpx.Response(
                self.create_status,
                json=self.create_body or None,
                headers=headers if self.create_status == 201 else {},
            )
        if request.method == "DELETE":
            return httpx.Response(self.delete_status)
        return httpx.Response(404)

    def provider(self, **overrides) -> KeycloakIdentityProvider:
        client = httpx.AsyncClient(transport=httpx.MockTransport(self.handler))
        return KeycloakIdentityProvider(
            base_url="http://kc",
            realm="agilina",
            client_id="agilina-api",
            client_secret="the-secret",
            client=client,
            **overrides,
        )


async def _create(provider: KeycloakIdentityProvider, **overrides):
    fields = {
        "email": Email("julian@example.test"),
        "full_name": "Julián Torres",
        "password": PASSWORD,
    }
    fields.update(overrides)
    return await provider.create_user(**fields)


def test_a_full_name_is_split_into_the_first_word_and_the_rest():
    assert split_name("Julián Torres") == ("Julián", "Torres")
    assert split_name("  María  de los Ángeles Ruiz ") == ("María", "de los Ángeles Ruiz")
    assert split_name("Cher") == ("Cher", "")


async def test_a_created_user_is_enabled_verified_and_has_a_permanent_password():
    keycloak = FakeKeycloak()

    subject = await _create(keycloak.provider())

    assert subject == USER_ID  # taken from the Location header: it is the `sub` claim
    create = next(r for r in keycloak.requests if r.url.path.endswith("/users"))
    body = json.loads(create.content)
    assert body["username"] == body["email"] == "julian@example.test"
    assert (body["firstName"], body["lastName"]) == ("Julián", "Torres")
    assert body["enabled"] is True and body["emailVerified"] is True
    assert body["credentials"] == [{"type": "password", "value": PASSWORD, "temporary": False}]
    assert create.headers["Authorization"] == "Bearer token-1"


async def test_it_authenticates_as_its_own_client_with_client_credentials():
    keycloak = FakeKeycloak()
    await _create(keycloak.provider())

    token_request = keycloak.requests[0]

    assert token_request.url.path == "/realms/agilina/protocol/openid-connect/token"
    form = dict(item.split("=") for item in token_request.content.decode().split("&"))
    assert form == {
        "grant_type": "client_credentials",
        "client_id": "agilina-api",
        "client_secret": "the-secret",
    }


async def test_the_token_is_reused_until_it_is_about_to_expire():
    keycloak = FakeKeycloak()
    provider = keycloak.provider()

    await _create(provider)
    await _create(provider, email=Email("laura@example.test"))
    assert keycloak.token_calls == 1

    keycloak.expires_in = 900
    provider._token_expires_at = 0.0  # the clock moved past the expiry
    await _create(provider, email=Email("diego@example.test"))
    assert keycloak.token_calls == 2


async def test_a_token_that_keycloak_rejects_is_renewed_once_and_the_call_repeated():
    keycloak = FakeKeycloak()
    keycloak.reject_next_tokens = 1

    subject = await _create(keycloak.provider())

    assert subject == USER_ID and keycloak.token_calls == 2


@pytest.mark.parametrize(
    ("error", "reason"),
    [
        ("invalidPasswordMinLengthMessage", "min_length"),
        ("invalidPasswordNotUsernameMessage", "not_username"),
        ("invalidPasswordNotEmailMessage", "not_email"),
        ("invalidPasswordHistoryMessage", "other"),
    ],
)
async def test_a_refused_password_comes_back_as_a_stable_reason(error, reason):
    keycloak = FakeKeycloak()
    keycloak.create_status = 400
    keycloak.create_body = {"error": error, "error_description": "Invalid password: ..."}

    with pytest.raises(PasswordPolicyError) as raised:
        await _create(keycloak.provider())

    assert raised.value.reasons == (reason,)


async def test_an_email_keycloak_already_has_is_an_existing_account():
    keycloak = FakeKeycloak()
    keycloak.create_status = 409
    keycloak.create_body = {"errorMessage": "User exists with same email"}

    with pytest.raises(AccountAlreadyExistsError):
        await _create(keycloak.provider())


@pytest.mark.parametrize("status", [400, 403, 500, 503])
async def test_any_other_failure_is_an_outage_and_never_echoes_the_password(status):
    keycloak = FakeKeycloak()
    keycloak.create_status = status
    keycloak.create_body = {"error": "something", "echo": PASSWORD}

    with pytest.raises(IdentityProviderUnavailableError) as raised:
        await _create(keycloak.provider())

    assert str(status) in str(raised.value) and PASSWORD not in str(raised.value)


async def test_a_token_request_that_fails_is_an_outage():
    keycloak = FakeKeycloak()
    keycloak.token_status = 401

    with pytest.raises(IdentityProviderUnavailableError, match="token"):
        await _create(keycloak.provider())


async def test_a_network_failure_is_an_outage():
    def refuse(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("connection refused")

    provider = KeycloakIdentityProvider(
        base_url="http://kc",
        realm="agilina",
        client_id="agilina-api",
        client_secret="s",
        client=httpx.AsyncClient(transport=httpx.MockTransport(refuse)),
    )

    with pytest.raises(IdentityProviderUnavailableError, match="did not answer"):
        await _create(provider)


async def test_deleting_a_user_works_and_deleting_one_that_is_gone_is_not_an_error():
    keycloak = FakeKeycloak()
    provider = keycloak.provider()

    await provider.delete_user(USER_ID)
    keycloak.delete_status = 404
    await provider.delete_user(USER_ID)

    deletes = [r for r in keycloak.requests if r.method == "DELETE"]
    assert [r.url.path for r in deletes] == [f"/admin/realms/agilina/users/{USER_ID}"] * 2


async def test_a_failed_deletion_is_reported():
    keycloak = FakeKeycloak()
    keycloak.delete_status = 500

    with pytest.raises(IdentityProviderUnavailableError):
        await keycloak.provider().delete_user(USER_ID)


def _provider_answering(admin_answer) -> KeycloakIdentityProvider:
    """Keycloak hands out tokens normally; ``admin_answer`` decides every Admin API call."""

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("/protocol/openid-connect/token"):
            return httpx.Response(200, json={"access_token": "token", "expires_in": 900})
        return admin_answer(request)

    return KeycloakIdentityProvider(
        base_url="http://kc",
        realm="agilina",
        client_id="agilina-api",
        client_secret="s",
        client=httpx.AsyncClient(transport=httpx.MockTransport(handler)),
    )


async def test_a_network_failure_on_the_admin_call_is_an_outage():
    def refuse(request: httpx.Request) -> httpx.Response:
        raise httpx.ReadTimeout("too slow")

    with pytest.raises(IdentityProviderUnavailableError, match="did not answer"):
        await _create(_provider_answering(refuse))


async def test_a_created_user_without_a_location_is_an_outage_because_the_subject_is_unknown():
    provider = _provider_answering(lambda request: httpx.Response(201))

    with pytest.raises(IdentityProviderUnavailableError, match="which user"):
        await _create(provider)


async def test_a_bad_request_that_is_not_json_is_an_outage_not_a_password_problem():
    provider = _provider_answering(lambda request: httpx.Response(400, text="<html>oops</html>"))

    with pytest.raises(IdentityProviderUnavailableError):
        await _create(provider)


async def test_closing_the_adapter_closes_its_http_client():
    provider = _provider_answering(lambda request: httpx.Response(204))

    await provider.aclose()

    assert provider._client.is_closed is True  # noqa: SLF001
