"""The teams HTTP API, with in-memory doubles behind the use cases and the access ports."""

import logging

import pytest
from httpx import ASGITransport, AsyncClient

from agilina_api.bootstrap.app import create_app
from agilina_api.shared.presentation.http.access import get_authenticated_users, get_team_access
from agilina_api.teams.application.commands.change_member_role import ChangeMemberRoleHandler
from agilina_api.teams.application.commands.create_team_as_admin import CreateTeamAsAdminHandler
from agilina_api.teams.application.commands.remove_member import RemoveMemberHandler
from agilina_api.teams.application.dtos import MemberContact, MemberRecord, TeamView, UserTeamView
from agilina_api.teams.application.queries.get_team import GetTeamHandler
from agilina_api.teams.application.queries.list_my_teams import ListMyTeamsHandler
from agilina_api.teams.application.queries.list_team_members import ListTeamMembersHandler
from agilina_api.teams.presentation.http import dependencies as deps
from agilina_shared.enums import Language, OperationMode, TeamRole
from tests.api.builders import NOW, TeamBuilder, next_id
from tests.api.doubles import (
    FakeActiveSprints,
    FakeAuthenticatedUsers,
    FakeClock,
    FakeMemberContacts,
    FakeTeamAccess,
    FakeTeamQueries,
    FakeTeamsUnitOfWork,
)

TOKEN_ANA = "token-of-ana"
TOKEN_BRUNO = "token-of-bruno"
TOKEN_CARLA = "token-of-carla"


def _returning(handler):
    """A provider that hands back this very object (see the identity router tests)."""
    return lambda: handler


class Api:
    """Ana is admin of Atlas and member of Boreal; Carla is a member of Atlas; Bruno has no
    team. The members of Atlas live in ``members_uow`` (commands) and in the queries."""

    def __init__(self) -> None:
        self.ana, self.bruno, self.carla = next_id(), next_id(), next_id()
        self.atlas, self.boreal = next_id(), next_id()
        self.uow = FakeTeamsUnitOfWork()
        self.members_uow = FakeTeamsUnitOfWork(sprints=FakeActiveSprints())
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
            members={
                self.atlas: (
                    MemberRecord(user_id=self.ana, role=TeamRole.ADMIN, joined_at=NOW),
                    MemberRecord(user_id=self.carla, role=TeamRole.MEMBER, joined_at=NOW),
                )
            },
        )
        contacts = FakeMemberContacts(
            {
                self.ana: MemberContact(full_name="Ana Gil", email="ana@example.test"),
                self.carla: MemberContact(full_name="Carla Ruiz", email="carla@example.test"),
            }
        )
        access = FakeTeamAccess(
            {
                (self.atlas, self.ana): TeamRole.ADMIN,
                (self.boreal, self.ana): TeamRole.MEMBER,
                (self.atlas, self.carla): TeamRole.MEMBER,
            }
        )
        users = FakeAuthenticatedUsers(
            {TOKEN_ANA: self.ana, TOKEN_BRUNO: self.bruno, TOKEN_CARLA: self.carla}
        )
        app = create_app()
        overrides = {
            deps.get_create_team_as_admin_handler: CreateTeamAsAdminHandler(
                lambda: self.uow, FakeClock(), new_id=next_id
            ),
            deps.get_list_my_teams_handler: ListMyTeamsHandler(self.queries),
            deps.get_get_team_handler: GetTeamHandler(self.queries),
            deps.get_list_team_members_handler: ListTeamMembersHandler(self.queries, contacts),
            deps.get_change_member_role_handler: ChangeMemberRoleHandler(
                lambda: self.members_uow, FakeClock()
            ),
            deps.get_remove_member_handler: RemoveMemberHandler(
                lambda: self.members_uow, FakeClock()
            ),
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

    def role_in_atlas(self, user_id) -> TeamRole | None:
        """The role stored by the commands, or ``None`` once the person left the team."""
        membership = self.members_uow.teams.teams[self.atlas].membership_of(user_id)
        assert membership is not None
        return membership.role if membership.is_active else None


@pytest.fixture
async def api() -> Api:
    api = Api()
    await (
        TeamBuilder()
        .with_id(api.atlas)
        .with_admin(api.ana)
        .with_member(api.carla)
        .saved_in(api.members_uow.teams)
    )
    return api


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
    assert response.json()["error"]["code"] == "invalid_team_name"
    assert response.headers["cache-control"] == "no-store"
    assert api.uow.teams.teams == {} and api.uow.committed is False


async def test_a_name_longer_than_80_answers_422_invalid_team_name(api):
    response = await api.request("POST", "", TOKEN_BRUNO, json={"name": "x" * 81})

    assert response.status_code == 422 and response.json()["error"]["code"] == "invalid_team_name"
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
    assert response.json()["error"]["code"] == "not_a_team_member"
    assert "Atlas" not in response.text


async def test_a_team_that_does_not_exist_answers_403_like_a_foreign_one(api):
    response = await api.request("GET", f"/{next_id()}", TOKEN_ANA)

    assert response.status_code == 403 and response.json()["error"]["code"] == "not_a_team_member"


async def test_a_member_of_a_team_that_vanished_gets_404_team_not_found(api):
    """A membership without its team cannot exist (foreign key): only a race gets here."""
    del api.queries.views[api.atlas]

    response = await api.request("GET", f"/{api.atlas}", TOKEN_ANA)

    assert response.status_code == 404 and response.json()["error"]["code"] == "team_not_found"


async def test_a_malformed_team_id_answers_422(api):
    response = await api.request("GET", "/not-a-uuid", TOKEN_ANA)

    assert response.status_code == 422


# -------------------------------------------------------------- authentication --
ROUTES = [("POST", "", {"json": {"name": "Cielo"}}), ("GET", "", {}), ("GET", "/{atlas}", {})]


@pytest.mark.parametrize(("method", "path", "kwargs"), ROUTES)
async def test_without_a_token_the_team_routes_answer_401(api, method, path, kwargs):
    response = await api.request(method, path.format(atlas=api.atlas), **kwargs)

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "not_authenticated"
    assert response.headers["www-authenticate"] == "Bearer"
    assert api.uow.teams.teams == {}


@pytest.mark.parametrize(("method", "path", "kwargs"), ROUTES)
async def test_an_invalid_token_answers_401(api, method, path, kwargs):
    response = await api.request(method, path.format(atlas=api.atlas), "forged-token", **kwargs)

    assert response.status_code == 401 and response.json()["error"]["code"] == "not_authenticated"
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
    assert "ErrorEnvelope" in spec["components"]["schemas"]


# ------------------------------------------------------------- members (HU-06) --
async def test_an_admin_lists_the_members_with_their_role_label_and_blockers(api):
    response = await api.request("GET", f"/{api.atlas}/members", TOKEN_ANA)

    assert response.status_code == 200
    assert response.json() == {
        "roles": [{"role": "admin", "label": "admin"}, {"role": "member", "label": "member"}],
        "members": [
            {
                "user_id": str(api.ana),
                "full_name": "Ana Gil",
                "email": "ana@example.test",
                "role": "admin",
                "label": "admin",
                "role_change_blocked_by": "last_admin",
                "removal_blocked_by": "last_admin",
            },
            {
                "user_id": str(api.carla),
                "full_name": "Carla Ruiz",
                "email": "carla@example.test",
                "role": "member",
                "label": "member",
                "role_change_blocked_by": None,
                "removal_blocked_by": None,
            },
        ],
    }


async def test_with_a_sprint_in_progress_the_list_says_no_role_can_change(api):
    api.queries.teams_with_active_sprint.add(api.atlas)

    members = (await api.request("GET", f"/{api.atlas}/members", TOKEN_ANA)).json()["members"]

    assert [m["role_change_blocked_by"] for m in members] == ["sprint_in_progress"] * 2
    assert [m["removal_blocked_by"] for m in members] == ["last_admin", None]


async def test_an_admin_changes_the_role_of_a_member(api):
    response = await api.request(
        "PATCH", f"/{api.atlas}/members/{api.carla}", TOKEN_ANA, json={"role": "admin"}
    )

    assert response.status_code == 204 and response.content == b""
    assert api.role_in_atlas(api.carla) is TeamRole.ADMIN
    assert api.members_uow.committed is True


async def test_the_admin_of_the_token_is_who_asked_for_a_role_change(api, caplog):
    with caplog.at_level(logging.INFO):
        await api.request(
            "PATCH", f"/{api.atlas}/members/{api.carla}", TOKEN_ANA, json={"role": "admin"}
        )

    assert f"user {api.ana} changed the role of user {api.carla}" in caplog.text


async def test_the_only_admin_cannot_demote_themselves_and_gets_409_last_admin(api):
    response = await api.request(
        "PATCH", f"/{api.atlas}/members/{api.ana}", TOKEN_ANA, json={"role": "member"}
    )

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "last_admin"
    assert api.role_in_atlas(api.ana) is TeamRole.ADMIN and api.members_uow.committed is False


async def test_with_a_sprint_in_progress_a_role_change_gets_409_sprint_in_progress(api):
    api.members_uow.sprints.teams_with_active_sprint.add(api.atlas)

    response = await api.request(
        "PATCH", f"/{api.atlas}/members/{api.carla}", TOKEN_ANA, json={"role": "admin"}
    )

    assert response.status_code == 409 and response.json()["error"]["code"] == "sprint_in_progress"
    assert api.role_in_atlas(api.carla) is TeamRole.MEMBER


async def test_changing_the_role_of_someone_outside_the_team_answers_404(api):
    response = await api.request(
        "PATCH", f"/{api.atlas}/members/{api.bruno}", TOKEN_ANA, json={"role": "admin"}
    )

    assert response.status_code == 404 and response.json()["error"]["code"] == "member_not_found"


@pytest.mark.parametrize(
    "body", [{}, {"role": "scrum_master"}, {"role": "admin", "team_id": "x"}, {"role": None}]
)
async def test_a_malformed_role_change_answers_422_and_changes_nothing(api, body):
    response = await api.request("PATCH", f"/{api.atlas}/members/{api.carla}", TOKEN_ANA, json=body)

    assert response.status_code == 422
    assert api.role_in_atlas(api.carla) is TeamRole.MEMBER and api.members_uow.committed is False


async def test_an_admin_removes_a_member(api):
    response = await api.request("DELETE", f"/{api.atlas}/members/{api.carla}", TOKEN_ANA)

    assert response.status_code == 204 and response.content == b""
    assert api.role_in_atlas(api.carla) is None and api.members_uow.committed is True


async def test_the_admin_of_the_token_is_who_asked_for_a_removal(api, caplog):
    with caplog.at_level(logging.INFO):
        await api.request("DELETE", f"/{api.atlas}/members/{api.carla}", TOKEN_ANA)

    assert f"user {api.ana} removed user {api.carla}" in caplog.text


async def test_a_sprint_in_progress_does_not_prevent_a_removal(api):
    api.members_uow.sprints.teams_with_active_sprint.add(api.atlas)

    response = await api.request("DELETE", f"/{api.atlas}/members/{api.carla}", TOKEN_ANA)

    assert response.status_code == 204 and api.role_in_atlas(api.carla) is None


async def test_the_only_admin_cannot_remove_themselves_and_gets_409_last_admin(api):
    response = await api.request("DELETE", f"/{api.atlas}/members/{api.ana}", TOKEN_ANA)

    assert response.status_code == 409 and response.json()["error"]["code"] == "last_admin"
    assert api.role_in_atlas(api.ana) is TeamRole.ADMIN


async def test_removing_someone_outside_the_team_answers_404(api):
    response = await api.request("DELETE", f"/{api.atlas}/members/{api.bruno}", TOKEN_ANA)

    assert response.status_code == 404 and response.json()["error"]["code"] == "member_not_found"


async def test_a_malformed_member_id_answers_422(api):
    response = await api.request("DELETE", f"/{api.atlas}/members/not-a-uuid", TOKEN_ANA)

    assert response.status_code == 422


MEMBER_ROUTES = [
    ("GET", "/{atlas}/members", {}),
    ("PATCH", "/{atlas}/members/{carla}", {"json": {"role": "admin"}}),
    ("DELETE", "/{atlas}/members/{carla}", {}),
]


def _path(api: Api, path: str) -> str:
    return path.format(atlas=api.atlas, carla=api.carla)


@pytest.mark.parametrize(("method", "path", "kwargs"), MEMBER_ROUTES)
async def test_a_member_who_is_not_an_admin_gets_403_not_a_team_admin(api, method, path, kwargs):
    response = await api.request(method, _path(api, path), TOKEN_CARLA, **kwargs)

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "not_a_team_admin"
    assert "Ana Gil" not in response.text
    assert api.role_in_atlas(api.carla) is TeamRole.MEMBER and api.members_uow.committed is False


@pytest.mark.parametrize(("method", "path", "kwargs"), MEMBER_ROUTES)
async def test_someone_outside_the_team_gets_403_not_a_team_member(api, method, path, kwargs):
    response = await api.request(method, _path(api, path), TOKEN_BRUNO, **kwargs)

    assert response.status_code == 403 and response.json()["error"]["code"] == "not_a_team_member"
    assert api.role_in_atlas(api.carla) is TeamRole.MEMBER


@pytest.mark.parametrize(("method", "path", "kwargs"), MEMBER_ROUTES)
async def test_admin_rights_in_one_team_do_not_reach_another(api, method, path, kwargs):
    """Ana is admin of Atlas but only a member of Boreal: Atlas' admin rights do not travel."""
    path = path.replace("{atlas}", str(api.boreal))

    response = await api.request(method, _path(api, path), TOKEN_ANA, **kwargs)

    assert response.status_code == 403 and response.json()["error"]["code"] == "not_a_team_admin"


@pytest.mark.parametrize(("method", "path", "kwargs"), MEMBER_ROUTES)
async def test_without_a_valid_token_the_member_routes_answer_401(api, method, path, kwargs):
    missing = await api.request(method, _path(api, path), **kwargs)
    forged = await api.request(method, _path(api, path), "forged-token", **kwargs)

    for response in (missing, forged):
        assert (
            response.status_code == 401 and response.json()["error"]["code"] == "not_authenticated"
        )
    assert api.role_in_atlas(api.carla) is TeamRole.MEMBER


async def test_the_openapi_documents_the_member_routes_and_their_errors(api):
    async with api.client() as client:
        spec = (await client.get("/openapi.json")).json()

    listing = spec["paths"]["/v1/teams/{team_id}/members"]["get"]
    assert {"200", "401", "403"} <= set(listing["responses"])
    member = spec["paths"]["/v1/teams/{team_id}/members/{user_id}"]
    assert {"204", "401", "403", "404", "409", "422"} <= set(member["patch"]["responses"])
    assert {"204", "401", "403", "404", "409", "422"} <= set(member["delete"]["responses"])
    assert "`not_a_team_admin`" in member["patch"]["responses"]["403"]["description"]
    assert "`last_admin`" in member["delete"]["responses"]["409"]["description"]
    assert "`sprint_in_progress`" in member["patch"]["responses"]["409"]["description"]
    blockers = spec["components"]["schemas"]["TeamMemberResponse"]["properties"]
    assert "`sprint_in_progress`" in blockers["role_change_blocked_by"]["description"]
