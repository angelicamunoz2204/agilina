"""A simulated realm: serves its key set the way Keycloak does, and counts the visits."""

import httpx

from tests.api.builders.access_token import SigningKey

JWKS_URL = "http://auth.internal/realms/agilina/protocol/openid-connect/certs"


class FakeRealmKeys:
    """What ``/protocol/openid-connect/certs`` answers. Keycloak also publishes an
    encryption key, so the double does too: the verifier must ignore it."""

    def __init__(self, *keys: SigningKey) -> None:
        self.keys = list(keys)
        self.reads = 0
        self.status = 200
        self.body: object | None = None
        self.unreachable = False

    def rotate_to(self, *keys: SigningKey) -> None:
        """Keycloak replaced its keys."""
        self.keys = list(keys)

    def handler(self, request: httpx.Request) -> httpx.Response:
        self.reads += 1
        if self.unreachable:
            raise httpx.ConnectError("connection refused")
        if self.body is not None:
            return httpx.Response(self.status, json=self.body)
        encryption_key = {"kid": "enc-1", "kty": "RSA", "alg": "RSA-OAEP", "use": "enc"}
        return httpx.Response(
            self.status, json={"keys": [*(key.jwk() for key in self.keys), encryption_key]}
        )

    def client(self) -> httpx.AsyncClient:
        return httpx.AsyncClient(transport=httpx.MockTransport(self.handler))
