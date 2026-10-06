"""Until login exists (HU-03) the API trusts no token: every route that needs a user is closed."""

import pytest
from httpx import AsyncClient

from agilina_api.bootstrap.authentication import ClosedAuthenticatedUsers
from tests.api.builders import next_id


@pytest.mark.parametrize("token", ["", "anything", "eyJhbGciOiJSUzI1NiJ9.e30.signature"])
async def test_the_closed_adapter_identifies_nobody(token):
    assert await ClosedAuthenticatedUsers().user_id_for(token) is None


@pytest.mark.parametrize(
    ("method", "path"), [("POST", "/v1/teams"), ("GET", "/v1/teams"), ("GET", "/v1/teams/{id}")]
)
async def test_with_the_real_wiring_every_team_route_answers_401_to_any_token(
    client: AsyncClient, method, path
):
    response = await client.request(
        method,
        path.format(id=next_id()),
        headers={"Authorization": "Bearer some-token"},
        json={"name": "Atlas"} if method == "POST" else None,
    )

    assert response.status_code == 401
    assert response.json()["code"] == "not_authenticated"
