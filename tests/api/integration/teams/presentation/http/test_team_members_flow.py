"""HU-06 end to end over HTTP: an admin manages the members of their team, with a real
PostgreSQL behind the API and the token doubled.

The story as the criteria tell it: the admin sees the members with name, email and role
(1); changes a role only without a sprint in progress, and the list says why the control
is disabled (3); removes someone, who stops being a member while their account stays (4);
the team never loses its last admin, not even by their own hand (5); and a member who calls
any of the routes directly gets 403 (6). The authorization is the backend's (DoD).

The Keycloak token check (HU-03) is doubled by ``FakeAuthenticatedUsers``; the
membership and the role are checked against ``team_member`` (``SqlTeamQueries``).
"""

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text

from agilina_api.bootstrap.app import create_app
from agilina_api.identity.presentation.http import dependencies as identity_deps
from agilina_api.shared.presentation.http.access import get_authenticated_users, get_team_access
from agilina_api.teams.application.queries.get_team import GetTeamHandler
from agilina_api.teams.domain.sprint import SprintStatus
from agilina_api.teams.presentation.http import dependencies as deps
from tests.api.builders import AppUserBuilder, TeamBuilder, next_id
from tests.api.doubles import FakeAuthenticatedUsers
from tests.api.integration.support import stored_sprint, stored_team, stored_user
from tests.api.integration.world import World

pytestmark = pytest.mark.integration

TOKEN_ANA = "token-of-ana"
TOKEN_BRUNO = "token-of-bruno"
TOKEN_CARLA = "token-of-carla"


def _returning(value):
    return lambda: value


class Members:
    """Atlas, administered by Ana, with Bruno as a member. Carla belongs to no team."""

    def __init__(self, world: World, team, ana, bruno, carla) -> None:
        self.world, self.team = world, team
        self.ana, self.bruno, self.carla = ana, bruno, carla
        app = create_app()
        overrides = {
            deps.get_list_team_members_handler: world.list_members,
            deps.get_change_member_role_handler: world.change_role,
            deps.get_remove_member_handler: world.remove,
            deps.get_get_team_handler: GetTeamHandler(world.team_queries),
            identity_deps.get_invite_to_team_handler: world.invite_to_team,
            get_authenticated_users: FakeAuthenticatedUsers(
                {TOKEN_ANA: ana.id, TOKEN_BRUNO: bruno.id, TOKEN_CARLA: carla.id}
            ),
            get_team_access: world.team_queries,
        }
        for provider, value in overrides.items():
            app.dependency_overrides[provider] = _returning(value)
        self.app = app

    async def request(self, method: str, path: str, token: str | None = TOKEN_ANA, **kwargs):
        headers = {} if token is None else {"Authorization": f"Bearer {token}"}
        async with AsyncClient(
            transport=ASGITransport(app=self.app), base_url="http://tests"
        ) as client:
            return await client.request(
                method, f"/v1/teams/{self.team.id}{path}", headers=headers, **kwargs
            )

    async def members(self, token: str = TOKEN_ANA) -> list[dict]:
        response = await self.request("GET", "/members", token)
        assert response.status_code == 200, response.text
        return response.json()["members"]

    async def change_role(self, user, role: str, token: str = TOKEN_ANA):
        return await self.request("PATCH", f"/members/{user.id}", token, json={"role": role})

    async def remove(self, user, token: str = TOKEN_ANA):
        return await self.request("DELETE", f"/members/{user.id}", token)


@pytest.fixture
async def members(session_factory) -> Members:
    ana = await stored_user(
        session_factory, AppUserBuilder().with_email("ana@example.test").named("Ana Gil")
    )
    bruno = await stored_user(
        session_factory, AppUserBuilder().with_email("bruno@example.test").named("Bruno Díaz")
    )
    carla = await stored_user(session_factory, AppUserBuilder().with_unique_email())
    team = await stored_team(
        session_factory, TeamBuilder().with_admin(ana.id).with_member(bruno.id)
    )
    return Members(World(session_factory), team, ana, bruno, carla)


async def _roles(engine, team_id) -> dict:
    async with engine.connect() as connection:
        rows = await connection.execute(
            text("SELECT user_id, role::text, status::text FROM team_member WHERE team_id = :id"),
            {"id": team_id},
        )
        return {row.user_id: (row.role, row.status) for row in rows}


# ------------------------------------------------------------- criterion 1 --
async def test_the_admin_sees_each_member_with_name_email_and_role(members):
    listed = await members.members()

    assert [(m["full_name"], m["email"], m["role"], m["label"]) for m in listed] == [
        ("Ana Gil", "ana@example.test", "admin", "admin"),
        ("Bruno Díaz", "bruno@example.test", "member", "member"),
    ]
    assert [m["user_id"] for m in listed] == [str(members.ana.id), str(members.bruno.id)]


# ------------------------------------------------------------- criterion 3 --
async def test_without_a_sprint_in_progress_the_admin_changes_a_role(members, engine):
    response = await members.change_role(members.bruno, "admin")

    assert response.status_code == 204
    assert (await _roles(engine, members.team.id))[members.bruno.id] == ("admin", "active")
    listed = await members.members()
    assert [m["role"] for m in listed] == ["admin", "admin"]
    assert [m["role_change_blocked_by"] for m in listed] == [None, None]


async def test_with_a_sprint_in_progress_the_role_cannot_change_and_the_list_says_why(
    members, engine, session_factory
):
    await stored_sprint(session_factory, members.team.id, SprintStatus.ACTIVE)

    response = await members.change_role(members.bruno, "admin")
    listed = await members.members()

    assert response.status_code == 409
    assert response.json() == {"code": "sprint_in_progress", "detail": "sprint in progress"}
    assert (await _roles(engine, members.team.id))[members.bruno.id] == ("member", "active")
    assert [m["role_change_blocked_by"] for m in listed] == ["sprint_in_progress"] * 2


async def test_once_the_sprint_is_closed_the_role_can_change_again(
    members, engine, session_factory
):
    sprint_id = await stored_sprint(session_factory, members.team.id, SprintStatus.ACTIVE)
    assert (await members.change_role(members.bruno, "admin")).status_code == 409
    async with engine.begin() as connection:
        await connection.execute(
            text("UPDATE sprint SET status = 'closed' WHERE id = :id"), {"id": sprint_id}
        )

    response = await members.change_role(members.bruno, "admin")

    assert response.status_code == 204
    assert (await _roles(engine, members.team.id))[members.bruno.id] == ("admin", "active")


async def test_the_sprint_of_another_team_does_not_block_this_one(members, engine, session_factory):
    other = await stored_team(session_factory, TeamBuilder().with_admin(members.carla.id))
    await stored_sprint(session_factory, other.id, SprintStatus.ACTIVE)

    response = await members.change_role(members.bruno, "admin")

    assert response.status_code == 204


# ------------------------------------------------------------- criterion 4 --
async def test_a_removed_member_leaves_the_team_but_keeps_their_account(members, engine):
    response = await members.remove(members.bruno)

    assert response.status_code == 204
    assert (await _roles(engine, members.team.id))[members.bruno.id] == ("member", "removed")
    assert [m["full_name"] for m in await members.members()] == ["Ana Gil"]
    async with engine.connect() as connection:
        accounts = (
            await connection.execute(
                text("SELECT is_active FROM app_user WHERE id = :id"), {"id": members.bruno.id}
            )
        ).scalar_one()
    assert accounts is True  # the account is identity's (and Keycloak's): it stays
    assert members.world.provider.deleted == [] and members.world.provider.created == []
    gone = await members.request("GET", "", TOKEN_BRUNO)
    assert gone.status_code == 403 and gone.json()["code"] == "not_a_team_member"


async def test_a_sprint_in_progress_does_not_prevent_a_removal(members, session_factory):
    await stored_sprint(session_factory, members.team.id, SprintStatus.ACTIVE)

    response = await members.remove(members.bruno)

    assert response.status_code == 204


async def test_removing_someone_who_is_not_a_member_answers_404(members):
    response = await members.remove(members.carla)

    assert response.status_code == 404 and response.json()["code"] == "member_not_found"


# ------------------------------------------------------- criterion 5 (DoD) --
async def test_the_only_admin_cannot_demote_themselves(members, engine):
    response = await members.change_role(members.ana, "member")

    assert response.status_code == 409
    assert response.json() == {"code": "last_admin", "detail": "last admin"}
    assert (await _roles(engine, members.team.id))[members.ana.id] == ("admin", "active")


async def test_the_only_admin_cannot_remove_themselves(members, engine):
    response = await members.remove(members.ana)

    assert response.status_code == 409 and response.json()["code"] == "last_admin"
    assert (await _roles(engine, members.team.id))[members.ana.id] == ("admin", "active")


async def test_the_list_tells_the_interface_the_only_admin_cannot_be_changed(members):
    ana, bruno = await members.members()

    assert (ana["role_change_blocked_by"], ana["removal_blocked_by"]) == ("last_admin",) * 2
    assert (bruno["role_change_blocked_by"], bruno["removal_blocked_by"]) == (None, None)


async def test_with_two_admins_one_can_step_down_and_then_the_other_cannot(members, engine):
    assert (await members.change_role(members.bruno, "admin")).status_code == 204

    stepped_down = await members.change_role(members.ana, "member")
    last = await members.change_role(members.bruno, "member", token=TOKEN_BRUNO)
    leaving = await members.remove(members.bruno, token=TOKEN_BRUNO)

    assert stepped_down.status_code == 204
    assert last.status_code == 409 and last.json()["code"] == "last_admin"
    assert leaving.status_code == 409 and leaving.json()["code"] == "last_admin"
    roles = await _roles(engine, members.team.id)
    assert roles == {members.ana.id: ("member", "active"), members.bruno.id: ("admin", "active")}


async def test_with_two_admins_one_can_remove_themselves(members, engine):
    assert (await members.change_role(members.bruno, "admin")).status_code == 204

    response = await members.remove(members.ana)

    assert response.status_code == 204
    assert (await _roles(engine, members.team.id))[members.ana.id] == ("admin", "removed")


# ------------------------------------------------------- criterion 6 (DoD) --
ROUTES = [
    ("GET", "/members", {}),
    ("PATCH", "/members/{bruno}", {"json": {"role": "admin"}}),
    ("DELETE", "/members/{bruno}", {}),
    ("POST", "/invitations", {"json": {"full_name": "Laura", "email": "laura@example.test"}}),
]


@pytest.mark.parametrize(("method", "path", "kwargs"), ROUTES)
async def test_a_member_calling_a_route_directly_gets_403_and_nothing_changes(
    members, engine, method, path, kwargs
):
    before = await _roles(engine, members.team.id)

    response = await members.request(
        method, path.format(bruno=members.bruno.id), TOKEN_BRUNO, **kwargs
    )

    assert response.status_code == 403
    assert response.json() == {"code": "not_a_team_admin", "detail": "not a team admin"}
    assert "Ana Gil" not in response.text
    assert await _roles(engine, members.team.id) == before
    assert members.world.mailer.sent == []


@pytest.mark.parametrize(("method", "path", "kwargs"), ROUTES)
async def test_someone_outside_the_team_gets_403_not_a_team_member(
    members, engine, method, path, kwargs
):
    before = await _roles(engine, members.team.id)

    response = await members.request(
        method, path.format(bruno=members.bruno.id), TOKEN_CARLA, **kwargs
    )

    assert response.status_code == 403 and response.json()["code"] == "not_a_team_member"
    assert await _roles(engine, members.team.id) == before


@pytest.mark.parametrize(("method", "path", "kwargs"), ROUTES)
async def test_without_a_token_every_route_answers_401(members, engine, method, path, kwargs):
    before = await _roles(engine, members.team.id)

    response = await members.request(method, path.format(bruno=members.bruno.id), None, **kwargs)

    assert response.status_code == 401 and response.json()["code"] == "not_authenticated"
    assert await _roles(engine, members.team.id) == before


async def test_a_removed_admin_loses_access_to_the_routes(members):
    assert (await members.change_role(members.bruno, "admin")).status_code == 204
    assert (await members.remove(members.bruno)).status_code == 204

    response = await members.request("GET", "/members", TOKEN_BRUNO)

    assert response.status_code == 403 and response.json()["code"] == "not_a_team_member"


async def test_a_team_that_does_not_exist_answers_like_someone_elses(members):
    async with AsyncClient(
        transport=ASGITransport(app=members.app), base_url="http://tests"
    ) as client:
        response = await client.get(
            f"/v1/teams/{next_id()}/members", headers={"Authorization": f"Bearer {TOKEN_ANA}"}
        )

    assert response.status_code == 403 and response.json()["code"] == "not_a_team_member"
