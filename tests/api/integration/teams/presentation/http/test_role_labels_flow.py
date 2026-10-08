"""HU-04 over HTTP with a real PostgreSQL: two roles are stored, the label is derived.

The story as the criteria tell it: exactly two roles are persisted per team (1); the admin is
shown as Scrum Master in a team in support mode (2) and as Administrator in an autonomous one
(3); changing the team's mode touches no role record (4); one user can be an admin here and a
member there, and each label is resolved team by team (5).

The Keycloak token check (HU-03) is doubled by ``FakeAuthenticatedUsers``.
"""

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text

from agilina_api.bootstrap.app import create_app
from agilina_api.shared.presentation.http.access import get_authenticated_users, get_team_access
from agilina_api.teams.application.queries.get_team import GetTeamHandler
from agilina_api.teams.application.queries.list_my_teams import ListMyTeamsHandler
from agilina_api.teams.presentation.http import dependencies as deps
from agilina_shared.enums import OperationMode
from tests.api.builders import AppUserBuilder, TeamBuilder
from tests.api.doubles import FakeAuthenticatedUsers
from tests.api.integration.support import stored_team, stored_user
from tests.api.integration.world import World

pytestmark = pytest.mark.integration

TOKEN = "token-of-ana"


def _returning(value):
    return lambda: value


class Labels:
    """Ana: admin of Atlas (support) and of Nova (autonomous), member of Boreal (autonomous)."""

    def __init__(self, world: World, ana, atlas, nova, boreal) -> None:
        self.ana, self.atlas, self.nova, self.boreal = ana, atlas, nova, boreal
        app = create_app()
        overrides = {
            deps.get_list_my_teams_handler: ListMyTeamsHandler(world.team_queries),
            deps.get_get_team_handler: GetTeamHandler(world.team_queries),
            deps.get_list_team_members_handler: world.list_members,
            get_authenticated_users: FakeAuthenticatedUsers({TOKEN: ana.id}),
            get_team_access: world.team_queries,
        }
        for provider, value in overrides.items():
            app.dependency_overrides[provider] = _returning(value)
        self.app = app

    async def get(self, path: str):
        async with AsyncClient(
            transport=ASGITransport(app=self.app), base_url="http://tests"
        ) as client:
            return await client.get(path, headers={"Authorization": f"Bearer {TOKEN}"})

    async def my_teams(self) -> dict[str, tuple[str, str, str]]:
        response = await self.get("/v1/teams")
        assert response.status_code == 200, response.text
        return {t["name"]: (t["role"], t["mode"], t["label"]) for t in response.json()}


@pytest.fixture
async def labels(session_factory) -> Labels:
    ana = await stored_user(
        session_factory, AppUserBuilder().with_email("ana@example.test").named("Ana Gil")
    )
    atlas = await stored_team(session_factory, TeamBuilder().named("Atlas").with_admin(ana.id))
    nova = await stored_team(
        session_factory,
        TeamBuilder().named("Nova").in_mode(OperationMode.AUTONOMOUS).with_admin(ana.id),
    )
    boreal = await stored_team(
        session_factory,
        TeamBuilder().named("Boreal").in_mode(OperationMode.AUTONOMOUS).with_member(ana.id),
    )
    return Labels(World(session_factory), ana, atlas, nova, boreal)


async def _member_rows(engine, team_id) -> list[tuple]:
    async with engine.connect() as connection:
        rows = await connection.execute(
            text("SELECT * FROM team_member WHERE team_id = :id ORDER BY id"), {"id": team_id}
        )
        return [tuple(row) for row in rows]


# ------------------------------------------------------------- criterion 1 --
async def test_exactly_two_roles_exist_and_no_label_is_stored(engine):
    async with engine.connect() as connection:
        roles = (
            await connection.execute(
                text(
                    "SELECT enumlabel FROM pg_enum e JOIN pg_type t ON t.oid = e.enumtypid "
                    "WHERE t.typname = 'team_role' ORDER BY enumsortorder"
                )
            )
        ).scalars()
        columns = (
            await connection.execute(
                text(
                    "SELECT column_name FROM information_schema.columns "
                    "WHERE table_name = 'team_member'"
                )
            )
        ).scalars()

    assert list(roles) == ["admin", "member"]
    assert not any("label" in column for column in columns)


# ------------------------------------------------- criteria 2, 3 and 5 --
async def test_the_same_user_is_labelled_team_by_team(labels):
    assert await labels.my_teams() == {
        "Atlas": ("admin", "support", "scrum_master"),
        "Nova": ("admin", "autonomous", "admin"),
        "Boreal": ("member", "autonomous", "member"),
    }


async def test_the_team_and_its_members_carry_the_same_label(labels):
    atlas = await labels.get(f"/v1/teams/{labels.atlas.id}")
    nova = await labels.get(f"/v1/teams/{labels.nova.id}")
    members = await labels.get(f"/v1/users?team_id={labels.atlas.id}")

    assert atlas.json()["label"] == "scrum_master"
    assert nova.json()["label"] == "admin"
    assert [m["label"] for m in members.json()["users"]] == ["scrum_master"]
    assert members.json()["roles"] == [
        {"role": "admin", "label": "scrum_master"},
        {"role": "member", "label": "member"},
    ]


# ------------------------------------------------------------- criterion 4 --
async def test_changing_the_mode_touches_no_role_record_and_changes_the_label(labels, engine):
    before = {t.id: await _member_rows(engine, t.id) for t in (labels.atlas, labels.nova)}

    async with engine.begin() as connection:
        await connection.execute(
            text("UPDATE team SET mode = 'autonomous' WHERE id = :id"), {"id": labels.atlas.id}
        )
        await connection.execute(
            text("UPDATE team SET mode = 'support' WHERE id = :id"), {"id": labels.nova.id}
        )

    after = {t.id: await _member_rows(engine, t.id) for t in (labels.atlas, labels.nova)}
    assert after == before
    teams = await labels.my_teams()
    assert teams["Atlas"] == ("admin", "autonomous", "admin")
    assert teams["Nova"] == ("admin", "support", "scrum_master")
    assert (await labels.get(f"/v1/users?team_id={labels.atlas.id}")).status_code == 200
