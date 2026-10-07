"""With the real wiring, a token that is not a Keycloak token identifies nobody (HU-03)."""

import pytest
from httpx import AsyncClient

from agilina_api.bootstrap.app import create_app
from tests.api.builders import next_id

# What is open on purpose, with the reason. Every other route needs a signed-in user: a route
# added tomorrow is closed until someone decides, here and on purpose, that it is not.
PUBLIC = {
    ("get", "/health"): "liveness probe",
    ("get", "/health/ready"): "readiness probe",
    ("post", "/v1/invitations/status"): "the invited person has no account yet",
    ("post", "/v1/invitations/activate"): "the invited person has no account yet",
    ("post", "/v1/invitations/request-new"): "the invited person has no account yet",
    ("get", "/v1/ceremonies/{ceremony_id}/context"): "worker contract, not implemented (HU-55)",
    ("post", "/v1/ceremonies/{ceremony_id}/result"): "worker contract, not implemented (HU-55)",
}


def _operations() -> list[tuple[str, str]]:
    paths = create_app().openapi()["paths"]
    return [(method, path) for path, methods in paths.items() for method in methods]


def test_the_public_routes_are_routes_that_exist():
    assert set(PUBLIC) <= set(_operations())


@pytest.mark.parametrize(
    ("method", "path"), [op for op in _operations() if op not in PUBLIC], ids=str
)
async def test_every_route_that_is_not_public_answers_401_without_a_token(
    client: AsyncClient, method, path
):
    response = await client.request(method, path.replace("{team_id}", str(next_id())))

    assert response.status_code == 401
    assert response.json()["code"] == "not_authenticated"
    assert response.headers["www-authenticate"] == "Bearer"


@pytest.mark.parametrize(
    "token", ["", "anything", "Bearer abc", "eyJhbGciOiJSUzI1NiJ9.e30.signature", "a.b.c"]
)
async def test_a_token_that_is_not_one_of_keycloak_answers_401(client: AsyncClient, token):
    response = await client.get("/v1/teams", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 401
    assert response.json()["code"] == "not_authenticated"
