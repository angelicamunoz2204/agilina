"""The teams HTTP API, with in-memory doubles behind the use cases and the access ports."""

import pytest
from httpx import ASGITransport, AsyncClient

from agilina_api.bootstrap.app import create_app
from agilina_api.shared.presentation.http.access import get_authenticated_users, get_team_access
from agilina_api.teams.application.commands.create_team_as_admin import CreateTeamAsAdminHandler
from agilina_api.teams.application.dtos import TeamView, UserTeamView
from agilina_api.teams.application.queries.get_team import GetTeamHandler
from agilina_api.teams.application.queries.list_my_teams import ListMyTeamsHandler
from agilina_api.teams.presentation.http import dependencies as deps
from agilina_shared.enums import Language, OperationMode, TeamRole
from tests.api.builders import next_id
from tests.api.doubles import (
    FakeAuthenticatedUsers,
    FakeClock,
    FakeTeamAccess,
    FakeTeamQueries,
    FakeTeamsUnitOfWork,
)

TOKEN_ANA = "token-of-ana"
TOKEN_BRUNO = "token-of-bruno"


def _returning(handler):
    """A provider that hands back this very object (see the identity router tests)."""
    return lambda: handler


class Api:
    """Ana is admin of Atlas and member of Boreal; Bruno has no team."""

    def __init__(self) -> None:
        self.ana, self.bruno = next_id(), next_id()
        self.atlas, self.boreal = next_id(), next_id()
        self.uow = FakeTeamsUnitOfWork()
        self.queries = FakeTeamQueries(
            teams_by_user={
                self.ana: (
                    UserTeamView(team_id=self.atlas, name="Atlas", role=TeamRole.ADMIN),
                    UserTeamView(team_id=self.boreal, name="Boreal", role=TeamRole.MEMBER),
                )
            },
            views={
                self.atlas: TeamView(
                    team_id=self.atlas,
                    name="Atlas",
                    mode=OperationMode.SUPPORT,
                    language=Language.EN,
                ),
                self.boreal: TeamView(
                    team_id=self.boreal,
                    name="Boreal",
                    mode=OperationMode.AUTONOMOUS,
                    language=Language.ES,
                ),
            },
        )
        access = FakeTeamAccess(
            {(self.atlas, self.ana): TeamRole.ADMIN, (self.boreal, self.ana): TeamRole.MEMBER}
        )
        users = FakeAuthenticatedUsers({TOKEN_ANA: self.ana, TOKEN_BRUNO: self.bruno})
        app = create_app()
        overrides = {
            deps.get_create_team_as_admin_handler: CreateTeamAsAdminHandler(
                lambda: self.uow, FakeClock(), new_id=next_id
            ),
            deps.get_list_my_teams_handler: ListMyTeamsHandler(self.queries),
            deps.get_get_team_handler: GetTeamHandler(self.queries),
            get_authenticated_users: users,
            get_team_access: access,
        }
        for provider, value in overrides.items():
            app.dependency_overrides[provider] = _returning(value)
        self.app = app

    def client(self) -> AsyncClient:
        return AsyncClient(transport=ASGITransport(app=self.app), base_url="http://tests")

    async def request(self, method: str, path: str, token: str | None = None, **kwargs):
        headers = {} if token is None else {"Authorization": f"Bearer {token}"}
        async with self.client() as client:
            return await client.request(method, f"/v1/teams{path}", headers=headers, **kwargs)


@pytest.fixture
def api() -> Api:
    return Api()


# ---------------------------------------------------------------------- create --
async def test_creating_a_team_answers_201_with_its_id_and_location(api):
    response = await api.request("POST", "", TOKEN_BRUNO, json={"name": "  Cielo  "})

    assert response.status_code == 201
    [team] = api.uow.teams.teams.values()
    assert response.json() == {"id": str(team.id)}
    assert response.headers["location"] == f"/v1/teams/{team.id}"
    assert team.name == "Cielo" and api.uow.committed is True


async def test_the_created_team_has_support_mode_english_and_its_creator_as_admin(api):
    await api.request("POST", "", TOKEN_BRUNO, json={"name": "Cielo"})

    [team] = api.uow.teams.teams.values()
    assert team.mode is OperationMode.SUPPORT and team.language is Language.EN
    membership = team.membership_of(api.bruno)
    assert membership is not None and membership.role is TeamRole.ADMIN
    assert team.created_by == api.bruno


async def test_the_creator_comes_from_the_token_not_from_the_body(api):
    response = await api.request(
        "POST", "", TOKEN_BRUNO, json={"name": "Cielo", "created_by": str(api.ana)}
    )

    assert response.status_code == 422
    assert api.uow.teams.teams == {}


@pytest.mark.parametrize("field", ["mode", "language", "role"])
async def test_the_defaults_cannot_be_chosen_in_the_body(api, field):
    response = await api.request("POST", "", TOKEN_BRUNO, json={"name": "Cielo", field: "x"})

    assert response.status_code == 422
    assert api.uow.teams.teams == {}


@pytest.mark.parametrize("name", ["", "   "])
async def test_a_blank_name_answers_422_invalid_team_name(api, name):
    response = await api.request("POST", "", TOKEN_BRUNO, json={"name": name})

    assert response.status_code == 422
    assert response.json() == {"code": "invalid_team_name", "detail": "invalid team name"}
    assert response.headers["cache-control"] == "no-store"
    assert api.uow.teams.teams == {} and api.uow.committed is False


async def test_a_name_longer_than_80_answers_422_invalid_team_name(api):
    response = await api.request("POST", "", TOKEN_BRUNO, json={"name": "x" * 81})

    assert response.status_code == 422 and response.json()["code"] == "invalid_team_name"
    assert api.uow.teams.teams == {}


async def test_a_name_of_80_characters_is_accepted(api):
    response = await api.request("POST", "", TOKEN_BRUNO, json={"name": "x" * 80})

    assert response.status_code == 201


async def test_a_body_without_a_name_answers_422(api):
    response = await api.request("POST", "", TOKEN_BRUNO, json={})

    assert response.status_code == 422
    assert api.uow.teams.teams == {}


# ------------------------------------------------------------------------ list --
async def test_listing_returns_id_name_and_role(api):
    response = await api.request("GET", "", TOKEN_ANA)

    assert response.status_code == 200
    assert response.json() == [
        {"id": str(api.atlas), "name": "Atlas", "role": "admin"},
        {"id": str(api.boreal), "name": "Boreal", "role": "member"},
    ]


async def test_a_user_without_teams_gets_an_empty_list(api):
    response = await api.request("GET", "", TOKEN_BRUNO)

    assert response.status_code == 200 and response.json() == []


# ------------------------------------------------------------------- read one --
async def test_a_member_reads_the_team_with_its_mode_language_and_role(api):
    atlas = await api.request("GET", f"/{api.atlas}", TOKEN_ANA)
    boreal = await api.request("GET", f"/{api.boreal}", TOKEN_ANA)

    assert atlas.status_code == 200
    assert atlas.json() == {
        "id": str(api.atlas),
        "name": "Atlas",
        "mode": "support",
        "language": "en",
        "role": "admin",
    }
    assert boreal.json()["role"] == "member" and boreal.json()["language"] == "es"


async def test_a_non_member_gets_403_when_reading_a_team(api):
    response = await api.request("GET", f"/{api.atlas}", TOKEN_BRUNO)

    assert response.status_code == 403
    assert response.json() == {"code": "not_a_team_member", "detail": "not a team member"}
    assert "Atlas" not in response.text


async def test_a_team_that_does_not_exist_answers_403_like_a_foreign_one(api):
    response = await api.request("GET", f"/{next_id()}", TOKEN_ANA)

    assert response.status_code == 403 and response.json()["code"] == "not_a_team_member"


async def test_a_member_of_a_team_that_vanished_gets_404_team_not_found(api):
    """A membership without its team cannot exist (foreign key): only a race gets here."""
    del api.queries.views[api.atlas]

    response = await api.request("GET", f"/{api.atlas}", TOKEN_ANA)

    assert response.status_code == 404 and response.json()["code"] == "team_not_found"


async def test_a_malformed_team_id_answers_422(api):
    response = await api.request("GET", "/not-a-uuid", TOKEN_ANA)

    assert response.status_code == 422


# -------------------------------------------------------------- authentication --
ROUTES = [("POST", "", {"json": {"name": "Cielo"}}), ("GET", "", {}), ("GET", "/{atlas}", {})]


@pytest.mark.parametrize(("method", "path", "kwargs"), ROUTES)
async def test_without_a_token_the_team_routes_answer_401(api, method, path, kwargs):
    response = await api.request(method, path.format(atlas=api.atlas), **kwargs)

    assert response.status_code == 401
    assert response.json()["code"] == "not_authenticated"
    assert response.headers["www-authenticate"] == "Bearer"
    assert api.uow.teams.teams == {}


@pytest.mark.parametrize(("method", "path", "kwargs"), ROUTES)
async def test_an_invalid_token_answers_401(api, method, path, kwargs):
    response = await api.request(method, path.format(atlas=api.atlas), "forged-token", **kwargs)

    assert response.status_code == 401 and response.json()["code"] == "not_authenticated"
    assert api.uow.teams.teams == {}


async def test_without_a_token_a_blank_name_still_answers_401(api):
    response = await api.request("POST", "", json={"name": "   "})

    assert response.status_code == 401


# ---------------------------------------------------------------------- contract --
async def test_the_openapi_documents_support_and_en_as_defaults_and_the_401_422_responses(api):
    async with api.client() as client:
        spec = (await client.get("/openapi.json")).json()

    create = spec["paths"]["/v1/teams"]["post"]
    assert {"201", "401", "422"} <= set(create["responses"])
    assert "`support`" in create["description"] and "`en`" in create["description"]
    assert "`admin`" in create["description"]
    assert (
        "80"
        in spec["components"]["schemas"]["CreateTeamRequest"]["properties"]["name"]["description"]
    )

    assert "401" in spec["paths"]["/v1/teams"]["get"]["responses"]

    read = spec["paths"]["/v1/teams/{team_id}"]["get"]
    assert {"200", "401", "403", "422"} <= set(read["responses"])
    assert [p["name"] for p in read["parameters"]] == ["team_id"]
    team = spec["components"]["schemas"]["TeamResponse"]["properties"]
    assert "`support`" in team["mode"]["description"]
    assert "`en`" in team["language"]["description"]

    assert spec["components"]["securitySchemes"]["HTTPBearer"]["scheme"] == "bearer"
    assert "ErrorResponse" in spec["components"]["schemas"]
