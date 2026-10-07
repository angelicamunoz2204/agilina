"""The token validation against the real Keycloak with the ``agilina`` realm imported.

Run with ``make test-keycloak``. They check what the simulated tests assume: that a token the
realm really signs for a person who signs in carries the issuer and the audience the API
expects, that nothing else the realm signs is accepted, and that a refused login says the
same whether or not the email exists.
"""

import base64
import hashlib
import html
import re
import secrets
import uuid
from urllib.parse import parse_qs, urlparse

import httpx
import pytest

from agilina_api.identity.domain.value_objects import Email
from agilina_api.identity.infrastructure.keycloak.access_token_verifier import (
    KeycloakAccessTokenVerifier,
)
from agilina_api.shared.infrastructure.clock import SystemClock

pytestmark = pytest.mark.keycloak

PASSWORD = "a-very-long-password-1"  # noqa: S105 - a test value
REDIRECT_URI = "http://localhost:4200/"


def _base64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


class Realm:
    """Signs people in the way the web application does: authorization code flow with PKCE,
    but speaking to Keycloak by its internal address (the page it serves names the public one)."""

    def __init__(self, settings, tenant: str) -> None:
        self.settings = settings
        self.realm_name = settings.tenant_realm(tenant)
        self.internal = settings.keycloak_url.rstrip("/")
        self.public = settings.keycloak_public_url.rstrip("/")
        self.base = f"{self.internal}/realms/{self.realm_name}/protocol/openid-connect"

    def verifier(self) -> KeycloakAccessTokenVerifier:
        return KeycloakAccessTokenVerifier(
            jwks_url=f"{self.base}/certs",
            issuer=f"{self.public}/realms/{self.realm_name}",
            audience=self.settings.keycloak_api_client,
            clock=SystemClock(),
        )

    async def login_page(self, client: httpx.AsyncClient, challenge: str) -> httpx.Response:
        return await client.get(
            f"{self.base}/auth",
            params={
                "client_id": self.settings.keycloak_web_client,
                "redirect_uri": REDIRECT_URI,
                "response_type": "code",
                "scope": "openid",
                "state": secrets.token_urlsafe(8),
                "code_challenge": challenge,
                "code_challenge_method": "S256",
            },
        )

    async def submit(
        self, client: httpx.AsyncClient, page: httpx.Response, email: str, password: str
    ) -> httpx.Response:
        match = re.search(r'<form id="kc-form-login"[^>]*action="([^"]+)"', page.text)
        assert match, "the login form was not found"
        action = html.unescape(match.group(1)).replace(self.public, self.internal)
        return await client.post(action, data={"username": email, "password": password})

    async def sign_in(self, email: str, password: str) -> dict:
        """The token response of a person who signs in with these credentials."""
        verifier = secrets.token_urlsafe(32)
        challenge = _base64url(hashlib.sha256(verifier.encode()).digest())
        async with httpx.AsyncClient(follow_redirects=False) as client:
            page = await self.login_page(client, challenge)
            assert page.status_code == 200
            answer = await self.submit(client, page, email, password)
            assert answer.status_code == 302, "the credentials were refused"
            code = parse_qs(urlparse(answer.headers["location"]).query)["code"][0]
            token = await client.post(
                f"{self.base}/token",
                data={
                    "grant_type": "authorization_code",
                    "code": code,
                    "redirect_uri": REDIRECT_URI,
                    "client_id": self.settings.keycloak_web_client,
                    "code_verifier": verifier,
                },
            )
        assert token.status_code == 200
        return token.json()

    async def refused_message(self, email: str, password: str) -> str:
        """The error the login page shows for these credentials."""
        challenge = _base64url(hashlib.sha256(b"x").digest())
        async with httpx.AsyncClient(follow_redirects=False) as client:
            page = await self.login_page(client, challenge)
            answer = await self.submit(client, page, email, password)
        assert answer.status_code == 200
        match = re.search(r'role="alert"[^>]*>\s*(.*?)\s*</div>', answer.text, re.DOTALL)
        assert match, "the page shows no error"
        return html.unescape(match.group(1))


@pytest.fixture
def realm(settings, tenant) -> Realm:
    return Realm(settings, tenant)


@pytest.fixture
async def person(provider, created) -> tuple[str, str]:
    """A person of the realm: ``(email, subject)``."""
    email = Email(f"it-{uuid.uuid4().hex[:10]}@example.test")
    subject = await provider.create_user(email=email, full_name="Julián Torres", password=PASSWORD)
    created.append(subject)
    return email.value, subject


async def test_the_access_token_a_person_gets_when_signing_in_is_valid_for_the_api(realm, person):
    email, subject = person
    verifier = realm.verifier()

    tokens = await realm.sign_in(email, PASSWORD)

    assert await verifier.verified_subject(tokens["access_token"]) == subject
    await verifier.aclose()


async def test_the_id_token_is_not_an_access_token(realm, person):
    email, _ = person
    verifier = realm.verifier()

    tokens = await realm.sign_in(email, PASSWORD)

    assert await verifier.verified_subject(tokens["id_token"]) is None
    await verifier.aclose()


async def test_a_token_that_was_tampered_with_is_refused(realm, person):
    email, _ = person
    verifier = realm.verifier()
    access_token = (await realm.sign_in(email, PASSWORD))["access_token"]
    header, payload, signature = access_token.split(".")
    flipped = ("A" if signature[0] != "A" else "B") + signature[1:]

    assert await verifier.verified_subject(f"{header}.{payload}.{flipped}") is None
    await verifier.aclose()


async def test_the_token_of_a_service_account_is_not_a_user_token(realm, provider):
    verifier = realm.verifier()
    service_token = await provider._access_token()  # noqa: SLF001

    assert await verifier.verified_subject(service_token) is None
    await verifier.aclose()


async def test_a_refused_login_says_the_same_whether_or_not_the_email_exists(realm, person):
    email, _ = person

    wrong_password = await realm.refused_message(email, "not-the-password")
    unknown_email = await realm.refused_message("nobody@example.test", "not-the-password")

    assert wrong_password == unknown_email
    assert email not in wrong_password


async def test_a_token_of_one_tenant_is_not_valid_in_another(settings, provider, created, tenant):
    """The realm of a tenant signs for its own people only: its issuer and its keys are its own."""
    other = "ecomoda" if tenant == "acme" else "acme"
    email = Email(f"it-{uuid.uuid4().hex[:10]}@example.test")
    created.append(
        await provider.create_user(email=email, full_name="Julián Torres", password=PASSWORD)
    )
    access_token = (await Realm(settings, tenant).sign_in(email.value, PASSWORD))["access_token"]
    own, foreign = Realm(settings, tenant).verifier(), Realm(settings, other).verifier()

    assert await own.verified_subject(access_token) is not None
    assert await foreign.verified_subject(access_token) is None
    await own.aclose()
    await foreign.aclose()


async def test_the_login_of_each_tenant_speaks_the_language_of_the_tenant(settings, tenant):
    challenge = _base64url(hashlib.sha256(b"x").digest())
    async with httpx.AsyncClient(follow_redirects=False) as client:
        page = await Realm(settings, tenant).login_page(client, challenge)

    expected = {"acme": "en", "ecomoda": "es"}[tenant]
    assert f'lang="{expected}"' in page.text
