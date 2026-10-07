"""HU-05 end to end over HTTP: real PostgreSQL behind the API, the token doubled.

The story as the criteria tell it: a user creates a team and becomes its admin, in support
mode and English; a blank name stores nothing; a user with several teams sees them all; and
nobody reaches a team they do not belong to (DoD).

Login does not exist yet (HU-03), so ``FakeAuthenticatedUsers`` stands for it: each token
is one stored user. Everything else is the real wiring: handlers, queries and the
membership check against ``team_member``.
"""

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text

from agilina_api.bootstrap.app import create_app
from agilina_api.shared.presentation.http.access import get_authenticated_users, get_team_access
from agilina_api.teams.application.commands.create_team_as_admin import CreateTeamAsAdminHandler
from agilina_api.teams.application.queries.get_team import GetTeamHandler
from agilina_api.teams.application.queries.list_my_teams import ListMyTeamsHandler
from agilina_api.teams.infrastructure.persistence.team_queries import SqlTeamQueries
from agilina_api.teams.infrastructure.persistence.unit_of_work import teams_unit_of_work_factory
from agilina_api.teams.presentation.http import dependencies as deps
from tests.api.builders import TeamBuilder, next_id
from tests.api.doubles import FakeAuthenticatedUsers, FakeClock
from tests.api.integration.support import removed_from_team, stored_team, stored_user

pytestmark = pytest.mark.integration

TOKEN_A = "token-of-ana"
TOKEN_B = "token-of-bruno"


def _returning(value):
    return lambda: value


class Teams:
    """The API wired to the test database, with Ana (token A) and Bruno (token B) stored."""

    def __init__(self, session_factory, ana, bruno) -> None:
        self.ana, self.bruno = ana, bruno
        queries = SqlTeamQueries(session_factory)
        app = create_app()
        overrides = {
            deps.get_create_team_as_admin_handler: CreateTeamAsAdminHandler(
                teams_unit_of_work_factory(session_factory), FakeClock()
            ),
            deps.get_list_my_teams_handler: ListMyTeamsHandler(queries),
            deps.get_get_team_handler: GetTeamHandler(queries),
            get_authenticated_users: FakeAuthenticatedUsers({TOKEN_A: ana, TOKEN_B: bruno}),
            get_team_access: queries,
        }
        for provider, value in overrides.items():
            app.dependency_overrides[provider] = _returning(value)
        self.app = app

    async def request(self, method: str, path: str = "", token: str | None = None, **kwargs):
        headers = {} if token is None else {"Authorization": f"Bearer {token}"}
        async with AsyncClient(
            transport=ASGITransport(app=self.app), base_url="http://tests"
        ) as client:
            return await client.request(method, f"/v1/teams{path}", headers=headers, **kwargs)

    async def create(self, name: str, token: str = TOKEN_A) -> str:
        response = await self.request("POST", "", token, json={"name": name})
        assert response.status_code == 201, response.text
        return str(response.json()["id"])


@pytest.fixture
async def teams(session_factory) -> Teams:
    ana = await stored_user(session_factory)
    bruno = await stored_user(session_factory)
    return Teams(session_factory, ana.id, bruno.id)


async def _count(engine, table: str) -> int:
    async with engine.connect() as connection:
        return (await connection.execute(text(f"SELECT count(*) FROM {table}"))).scalar_one()  # noqa: S608 - test constant


async def test_a_created_team_has_support_mode_and_english(teams, engine):
    team_id = await teams.create("  Atlas  ")

    response = await teams.request("GET", f"/{team_id}", TOKEN_A)

    assert response.status_code == 200
    assert response.json() == {
        "id": team_id,
        "name": "Atlas",
        "mode": "support",
        "language": "en",
        "role": "admin",
    }
    async with engine.connect() as connection:
        stored = (
            await connection.execute(
                text("SELECT mode::text, language::text, created_by FROM team WHERE id = :id"),
                {"id": team_id},
            )
        ).one()
    assert tuple(stored) == ("support", "en", teams.ana)


async def test_the_creator_is_admin_of_the_created_team(teams, engine):
    team_id = await teams.create("Atlas")

    async with engine.connect() as connection:
        members = (
            await connection.execute(
                text(
                    "SELECT user_id, role::text, status::text FROM team_member WHERE team_id = :id"
                ),
                {"id": team_id},
            )
        ).all()
    listed = (await teams.request("GET", "", TOKEN_A)).json()

    assert [tuple(member) for member in members] == [(teams.ana, "admin", "active")]
    assert listed == [{"id": team_id, "name": "Atlas", "role": "admin"}]


@pytest.mark.parametrize("name", ["", "   ", "x" * 81])
async def test_a_blank_name_is_rejected_and_nothing_is_stored(teams, engine, name):
    response = await teams.request("POST", "", TOKEN_A, json={"name": name})

    assert response.status_code == 422 and response.json()["error"]["code"] == "invalid_team_name"
    assert await _count(engine, "team") == 0
    assert await _count(engine, "team_member") == 0


async def test_a_user_with_several_teams_receives_them_all(teams, session_factory):
    boreal = await teams.create("boreal")
    atlas = await teams.create("Atlas")
    # Ana is also a member of a team Bruno administers (added the way an invitation does).
    cielo = await stored_team(
        session_factory,
        TeamBuilder().named("Cielo").created_with_admin(teams.bruno).with_member(teams.ana),
    )

    mine = await teams.request("GET", "", TOKEN_A)
    theirs = await teams.request("GET", "", TOKEN_B)

    assert mine.status_code == 200
    assert mine.json() == [
        {"id": atlas, "name": "Atlas", "role": "admin"},
        {"id": boreal, "name": "boreal", "role": "admin"},
        {"id": str(cielo.id), "name": "Cielo", "role": "member"},
    ]
    assert theirs.json() == [{"id": str(cielo.id), "name": "Cielo", "role": "admin"}]
    member_view = await teams.request("GET", f"/{cielo.id}", TOKEN_A)
    assert member_view.status_code == 200 and member_view.json()["role"] == "member"


async def test_a_user_without_teams_receives_an_empty_list(teams):
    response = await teams.request("GET", "", TOKEN_B)

    assert response.status_code == 200 and response.json() == []


async def test_a_user_of_team_a_asking_for_team_b_gets_403(teams):
    team_a = await teams.create("Atlas", token=TOKEN_A)
    team_b = await teams.create("Boreal", token=TOKEN_B)

    response = await teams.request("GET", f"/{team_b}", TOKEN_A)

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "not_a_team_member"
    assert "Boreal" not in response.text
    assert (await teams.request("GET", f"/{team_a}", TOKEN_A)).status_code == 200


def _without_request_id(response) -> dict:
    """The request id differs on every call; everything else must not."""
    error = response.json()["error"]
    return {key: value for key, value in error.items() if key != "request_id"}


async def test_a_team_that_does_not_exist_answers_like_someone_elses(teams):
    team_b = await teams.create("Boreal", token=TOKEN_B)

    foreign = await teams.request("GET", f"/{team_b}", TOKEN_A)
    missing = await teams.request("GET", f"/{next_id()}", TOKEN_A)

    assert missing.status_code == foreign.status_code == 403
    assert _without_request_id(missing) == _without_request_id(foreign)


async def test_a_removed_member_gets_403(teams, session_factory):
    team_id = await teams.create("Atlas")
    await removed_from_team(session_factory, team_id, teams.ana)

    response = await teams.request("GET", f"/{team_id}", TOKEN_A)
    listed = await teams.request("GET", "", TOKEN_A)

    assert response.status_code == 403 and response.json()["error"]["code"] == "not_a_team_member"
    assert listed.json() == []


async def test_without_a_token_every_team_route_answers_401(teams, engine):
    team_id = await teams.create("Atlas")

    responses = [
        await teams.request("POST", "", json={"name": "Boreal"}),
        await teams.request("GET", ""),
        await teams.request("GET", f"/{team_id}"),
        await teams.request("GET", f"/{team_id}", "forged-token"),
    ]

    for response in responses:
        assert response.status_code == 401
        assert response.json()["error"]["code"] == "not_authenticated"
        assert response.headers["www-authenticate"] == "Bearer"
    assert await _count(engine, "team") == 1
