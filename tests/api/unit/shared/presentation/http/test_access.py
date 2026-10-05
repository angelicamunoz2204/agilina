"""Who is calling (``current_user_id``) and whether they belong to the team of the route
(``current_team_member``), on a minimal application mounted by the test."""

from uuid import UUID

import pytest
from fastapi import Depends, FastAPI
from httpx import ASGITransport, AsyncClient

from agilina_api.shared.application.access import TeamContext
from agilina_api.shared.presentation.http.access import (
    current_team_member,
    current_user_id,
    get_authenticated_users,
    get_team_access,
)
from agilina_api.shared.presentation.http.errors import SHARED_ERRORS, register_error_handlers
from agilina_shared.enums import TeamRole
from tests.api.builders import next_id
from tests.api.doubles import FakeAuthenticatedUsers, FakeTeamAccess

TOKEN_A = "token-of-ana"
TOKEN_B = "token-of-bruno"


class Scenario:
    """Ana is admin of team A and Bruno is a member of team B."""

    def __init__(self) -> None:
        self.ana, self.bruno = next_id(), next_id()
        self.team_a, self.team_b = next_id(), next_id()
        self.users = FakeAuthenticatedUsers({TOKEN_A: self.ana, TOKEN_B: self.bruno})
        self.access = FakeTeamAccess(
            {
                (self.team_a, self.ana): TeamRole.ADMIN,
                (self.team_b, self.bruno): TeamRole.MEMBER,
            }
        )
        app = FastAPI()
        register_error_handlers(app, SHARED_ERRORS)
        app.dependency_overrides[get_authenticated_users] = lambda: self.users
        app.dependency_overrides[get_team_access] = lambda: self.access

        @app.get("/me")
        async def me(user_id: UUID = Depends(current_user_id)) -> dict[str, str]:
            return {"user_id": str(user_id)}

        @app.get("/teams/{team_id}/thing")
        async def thing(team: TeamContext = Depends(current_team_member)) -> dict[str, str]:
            return {"team_id": str(team.team_id), "user_id": str(team.user_id), "role": team.role}

        self.app = app

    async def get(self, path: str, token: str | None = None, scheme: str = "Bearer"):
        headers = {} if token is None else {"Authorization": f"{scheme} {token}"}
        async with AsyncClient(
            transport=ASGITransport(app=self.app), base_url="http://tests"
        ) as client:
            return await client.get(path, headers=headers)


@pytest.fixture
def scenario() -> Scenario:
    return Scenario()


def _assert_not_authenticated(response) -> None:
    assert response.status_code == 401
    assert response.json() == {"code": "not_authenticated", "detail": "not authenticated"}
    assert response.headers["www-authenticate"] == "Bearer"
    assert response.headers["cache-control"] == "no-store"


# ------------------------------------------------------------- current_user_id --
async def test_a_known_token_identifies_its_user(scenario):
    response = await scenario.get("/me", TOKEN_A)

    assert response.status_code == 200 and response.json() == {"user_id": str(scenario.ana)}


async def test_without_the_authorization_header_the_answer_is_401(scenario):
    _assert_not_authenticated(await scenario.get("/me"))


async def test_a_token_that_identifies_nobody_answers_401(scenario):
    _assert_not_authenticated(await scenario.get("/me", "forged-token"))


async def test_a_scheme_other_than_bearer_answers_401(scenario):
    _assert_not_authenticated(await scenario.get("/me", TOKEN_A, scheme="Basic"))


# --------------------------------------------------------- current_team_member --
async def test_a_member_of_the_team_gets_its_context_with_role(scenario):
    response = await scenario.get(f"/teams/{scenario.team_a}/thing", TOKEN_A)

    assert response.status_code == 200
    assert response.json() == {
        "team_id": str(scenario.team_a),
        "user_id": str(scenario.ana),
        "role": "admin",
    }


async def test_a_user_of_another_team_gets_403_not_a_team_member(scenario):
    response = await scenario.get(f"/teams/{scenario.team_b}/thing", TOKEN_A)

    assert response.status_code == 403
    assert response.json() == {"code": "not_a_team_member", "detail": "not a team member"}
    assert response.headers["cache-control"] == "no-store"


async def test_an_unknown_team_answers_403_like_a_foreign_one(scenario):
    foreign = await scenario.get(f"/teams/{scenario.team_b}/thing", TOKEN_A)
    unknown = await scenario.get(f"/teams/{next_id()}/thing", TOKEN_A)

    assert unknown.status_code == foreign.status_code == 403
    assert unknown.json() == foreign.json()


async def test_without_a_token_the_team_route_answers_401_before_checking_membership(scenario):
    _assert_not_authenticated(await scenario.get(f"/teams/{scenario.team_a}/thing"))
    _assert_not_authenticated(await scenario.get(f"/teams/{scenario.team_a}/thing", "forged"))


async def test_a_malformed_team_id_answers_422(scenario):
    response = await scenario.get("/teams/not-a-uuid/thing", TOKEN_A)

    assert response.status_code == 422


async def test_the_role_comes_from_the_stored_membership_of_that_team(scenario):
    scenario.access.roles[(scenario.team_b, scenario.ana)] = TeamRole.MEMBER

    in_a = await scenario.get(f"/teams/{scenario.team_a}/thing", TOKEN_A)
    in_b = await scenario.get(f"/teams/{scenario.team_b}/thing", TOKEN_A)

    assert in_a.json()["role"] == "admin" and in_b.json()["role"] == "member"
