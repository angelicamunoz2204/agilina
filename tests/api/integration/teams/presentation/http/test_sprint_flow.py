"""HU-07 end to end over HTTP: an admin configures the team's active sprint, with a real
PostgreSQL behind the API and the token doubled.

The story as the criteria tell it: the admin saves the sprint and the answer already carries
its day N of M (6), the dates and the participants are checked the same when the sprint is
started and when it is edited (1, 3), the order of the participants is the order of the turns
(4), and a team has a single active sprint, also when two admins save at once (5). Removing a
member takes them out of the daily and moves the next ones up; a new member is not added to
it on their own. Any member reads the sprint and its day; only an admin starts or edits it,
and someone outside the team reaches nothing. The authorization is the backend's.

The Keycloak token check (HU-03) is doubled by ``FakeAuthenticatedUsers``; the membership
and the role are checked against ``team_member`` (``SqlTeamQueries``). The index that keeps
one active sprint per team is shown refusing a direct insert in
``integration/migrations/test_migrations.py``
(``test_a_team_has_at_most_one_active_sprint_but_any_number_of_closed_ones``).
"""

import asyncio

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text

from agilina_api.bootstrap.app import create_app
from agilina_api.identity.application.commands.activate_account import ActivateAccount
from agilina_api.shared.presentation.http.access import get_authenticated_users, get_team_access
from agilina_api.teams.presentation.http import dependencies as deps
from tests.api.builders import AppUserBuilder, TeamBuilder
from tests.api.doubles import FakeAuthenticatedUsers
from tests.api.integration.support import stored_team, stored_user
from tests.api.integration.world import PASSWORD, TOKEN, World

pytestmark = pytest.mark.integration

TOKEN_ANA = "token-of-ana"
TOKEN_BRUNO = "token-of-bruno"
TOKEN_CARLA = "token-of-carla"

START, END = "2026-10-05", "2026-10-16"  # Monday to Friday of the next week: 12 days
DAILY_AT, TIME_ZONE = "2026-10-05T14:00:00Z", "America/Bogota"  # 09:00 in Bogotá (UTC-5)


def _returning(value):
    return lambda: value


class Sprints:
    """Atlas, administered by Ana, with Bruno and Dora as members. Carla belongs to no team.
    The clock is ``World``'s: Sunday 2026-10-04 at 12:00Z, the day before the sprint starts."""

    def __init__(self, world: World, team, ana, bruno, carla, dora) -> None:
        self.world, self.team = world, team
        self.ana, self.bruno, self.carla, self.dora = ana, bruno, carla, dora
        app = create_app()
        overrides = {
            deps.get_start_sprint_handler: world.start_sprint,
            deps.get_reconfigure_sprint_handler: world.reconfigure_sprint,
            deps.get_get_active_sprint_handler: world.active_sprint,
            deps.get_remove_member_handler: world.remove,
            get_authenticated_users: FakeAuthenticatedUsers(
                {TOKEN_ANA: ana.id, TOKEN_BRUNO: bruno.id, TOKEN_CARLA: carla.id}
            ),
            get_team_access: world.team_queries,
        }
        for provider, value in overrides.items():
            app.dependency_overrides[provider] = _returning(value)
        self.app = app

    async def request(self, method: str, path: str, token: str = TOKEN_ANA, **kwargs):
        async with AsyncClient(
            transport=ASGITransport(app=self.app), base_url="http://tests"
        ) as client:
            return await client.request(
                method,
                f"/v1/teams/{self.team.id}{path}",
                headers={"Authorization": f"Bearer {token}"},
                **kwargs,
            )

    async def start(self, body: dict, token: str = TOKEN_ANA):
        return await self.request("POST", "/sprints", token, json=body)

    async def edit(self, body: dict, token: str = TOKEN_ANA):
        return await self.request("PUT", "/sprints/active", token, json=body)

    async def read(self, token: str = TOKEN_ANA):
        return await self.request("GET", "/sprints/active", token)

    async def active(self) -> dict | None:
        """The active sprint as the admin reads it."""
        response = await self.read()
        assert response.status_code == 200, response.text
        return response.json()

    async def turns(self) -> list[tuple]:
        """The daily's participants of the active sprint, ``(user_id, turn_order)``."""
        sprint = await self.active()
        assert sprint is not None
        return [(p["user_id"], p["turn_order"]) for p in sprint["participants"]]

    async def remove(self, user, token: str = TOKEN_ANA):
        return await self.request("DELETE", f"/members/{user.id}", token)


def _body(*participants, start=START, end=END, daily_time=DAILY_AT, time_zone=TIME_ZONE) -> dict:
    """What the web sends to start or edit the sprint; the participants in turn order."""
    return {
        "start_date": start,
        "end_date": end,
        "daily_time": daily_time,
        "time_zone": time_zone,
        "participants": [str(user.id) for user in participants],
    }


@pytest.fixture
async def sprints(session_factory) -> Sprints:
    ana = await stored_user(
        session_factory, AppUserBuilder().with_email("ana@example.test").named("Ana Gil")
    )
    bruno, carla, dora = [
        await stored_user(session_factory, AppUserBuilder().with_unique_email()) for _ in range(3)
    ]
    team = await stored_team(
        session_factory,
        TeamBuilder().with_admin(ana.id).with_member(bruno.id).with_member(dora.id),
    )
    return Sprints(World(session_factory), team, ana, bruno, carla, dora)


async def _stored_sprints(engine, team_id) -> list[tuple]:
    """Every sprint of the team as stored, ``(id, status, start_date, end_date, time_zone)``."""
    async with engine.connect() as connection:
        rows = await connection.execute(
            text(
                "SELECT id::text, status::text, start_date::text, end_date::text, "
                "daily_time_zone FROM sprint WHERE team_id = :id ORDER BY created_at"
            ),
            {"id": team_id},
        )
        return [tuple(row) for row in rows]


async def _stored_turns(engine, team_id) -> list[tuple]:
    """The participants of the team's active sprint as stored, in turn order."""
    async with engine.connect() as connection:
        rows = await connection.execute(
            text(
                "SELECT p.user_id::text, p.turn_order FROM sprint_participant p "
                "JOIN sprint s ON s.id = p.sprint_id "
                "WHERE s.team_id = :id AND s.status = 'active' ORDER BY p.turn_order"
            ),
            {"id": team_id},
        )
        return [tuple(row) for row in rows]


# ---------------------------------------------------------- criteria 1-4, 6 --
async def test_an_admin_starts_a_sprint_and_the_response_carries_its_day(sprints, engine):
    response = await sprints.start(_body(sprints.dora, sprints.ana, sprints.bruno))

    assert response.status_code == 201, response.text
    started = response.json()
    assert response.headers["Location"] == f"/v1/teams/{sprints.team.id}/sprints/active"
    assert started["day"] == {"number": 0, "total": 12, "phase": "not_started"}
    assert (started["start_date"], started["end_date"]) == (START, END)
    assert (started["daily_time"], started["time_zone"]) == (DAILY_AT, TIME_ZONE)
    assert started["next_daily_at"] == DAILY_AT
    assert [(p["user_id"], p["turn_order"]) for p in started["participants"]] == [
        (str(sprints.dora.id), 1),
        (str(sprints.ana.id), 2),
        (str(sprints.bruno.id), 3),
    ]
    assert await sprints.active() == started
    assert await _stored_sprints(engine, sprints.team.id) == [
        (started["id"], "active", START, END, TIME_ZONE)
    ]


async def test_the_day_the_api_answers_follows_the_clock_in_the_daily_time_zone(sprints):
    assert (await sprints.start(_body(sprints.ana))).status_code == 201

    sprints.world.clock.advance(days=6, hours=3)  # Saturday 2026-10-10, 10:00 in Bogotá
    on_saturday = await sprints.active()
    sprints.world.clock.advance(days=7)  # Saturday 2026-10-17, the day after the last one
    after_the_end = await sprints.active()

    assert on_saturday is not None and after_the_end is not None
    assert on_saturday["day"] == {"number": 6, "total": 12, "phase": "in_progress"}
    assert on_saturday["next_daily_at"] == "2026-10-11T14:00:00Z"  # Sunday counts too
    assert after_the_end["day"] == {"number": 12, "total": 12, "phase": "finished"}
    assert after_the_end["next_daily_at"] is None


async def test_without_an_active_sprint_the_read_answers_null(sprints):
    response = await sprints.read(TOKEN_BRUNO)

    assert response.status_code == 200
    assert response.json() is None


async def test_the_admin_edits_the_active_sprint_and_it_keeps_its_id(sprints, engine):
    started = (await sprints.start(_body(sprints.ana, sprints.bruno))).json()

    response = await sprints.edit(
        _body(
            sprints.bruno,
            sprints.dora,
            end="2026-10-23",
            daily_time="2026-10-04T23:00:00Z",  # 08:00 of Monday 2026-10-05 in Tokyo
            time_zone="Asia/Tokyo",
        )
    )

    assert response.status_code == 200, response.text
    edited = response.json()
    assert edited["id"] == started["id"]
    assert edited["day"] == {"number": 0, "total": 19, "phase": "not_started"}
    assert edited["next_daily_at"] == "2026-10-04T23:00:00Z"
    assert [p["user_id"] for p in edited["participants"]] == [
        str(sprints.bruno.id),
        str(sprints.dora.id),
    ]
    assert await sprints.active() == edited
    assert await _stored_sprints(engine, sprints.team.id) == [
        (started["id"], "active", START, "2026-10-23", "Asia/Tokyo")
    ]


RULES = [
    pytest.param(
        lambda s: _body(s.ana, start="2026-10-16", end="2026-10-05"),
        "sprint_ends_before_start",
        id="ends-before-start",
    ),
    pytest.param(
        lambda s: _body(s.ana, time_zone="Mars/Olympus_Mons"),
        "invalid_time_zone",
        id="unknown-time-zone",
    ),
    pytest.param(lambda s: _body(), "no_daily_participants", id="no-participants"),
    pytest.param(lambda s: _body(s.ana, s.bruno, s.ana), "duplicate_daily_participant", id="twice"),
    pytest.param(
        lambda s: _body(s.ana, s.carla), "daily_participant_not_a_member", id="not-a-member"
    ),
]


@pytest.mark.parametrize(("body", "code"), RULES)
async def test_starting_a_sprint_that_breaks_a_rule_stores_nothing(sprints, engine, body, code):
    response = await sprints.start(body(sprints))

    assert response.status_code == 422
    assert response.json()["error"]["code"] == code
    assert await _stored_sprints(engine, sprints.team.id) == []
    assert await sprints.active() is None


@pytest.mark.parametrize(("body", "code"), RULES)
async def test_editing_validates_like_starting(sprints, engine, body, code):
    saved = (await sprints.start(_body(sprints.ana, sprints.bruno))).json()

    response = await sprints.edit(body(sprints))

    assert response.status_code == 422
    assert response.json()["error"]["code"] == code
    assert await sprints.active() == saved
    assert await _stored_turns(engine, sprints.team.id) == [
        (str(sprints.ana.id), 1),
        (str(sprints.bruno.id), 2),
    ]


async def test_a_member_who_left_the_team_cannot_be_added_to_the_daily(sprints):
    assert (await sprints.remove(sprints.dora)).status_code == 204

    response = await sprints.start(_body(sprints.ana, sprints.dora))

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "daily_participant_not_a_member"


# ------------------------------------------------------------- criterion 5 --
async def test_a_second_active_sprint_is_refused_with_409(sprints, engine):
    first = (await sprints.start(_body(sprints.ana))).json()

    response = await sprints.start(_body(sprints.bruno, start="2026-10-19", end="2026-10-30"))

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "active_sprint_exists"
    assert await _stored_sprints(engine, sprints.team.id) == [
        (first["id"], "active", START, END, TIME_ZONE)
    ]
    assert await sprints.active() == first


async def test_two_simultaneous_starts_leave_one_sprint_and_a_409_never_a_500(sprints, engine):
    responses = await asyncio.gather(
        sprints.start(_body(sprints.ana, sprints.bruno)),
        sprints.start(_body(sprints.dora, start="2026-10-12", end="2026-10-23")),
    )

    assert sorted(r.status_code for r in responses) == [201, 409]
    (started,) = [r.json() for r in responses if r.status_code == 201]
    (refused,) = [r.json() for r in responses if r.status_code == 409]
    assert refused["error"]["code"] == "active_sprint_exists"
    stored = await _stored_sprints(engine, sprints.team.id)
    assert [(sprint_id, status) for sprint_id, status, *_ in stored] == [(started["id"], "active")]
    assert await sprints.active() == started


# --------------------------------------------------- the members of the team --
async def test_removing_a_member_takes_them_out_of_the_daily_and_compacts_the_order(
    sprints, engine
):
    await sprints.start(_body(sprints.ana, sprints.bruno, sprints.dora))

    response = await sprints.remove(sprints.bruno)

    assert response.status_code == 204
    expected = [(str(sprints.ana.id), 1), (str(sprints.dora.id), 2)]
    assert await sprints.turns() == expected
    assert await _stored_turns(engine, sprints.team.id) == expected


async def test_removing_the_only_participant_leaves_the_daily_empty(sprints):
    await sprints.start(_body(sprints.bruno))

    response = await sprints.remove(sprints.bruno)

    assert response.status_code == 204
    assert await sprints.turns() == []


async def test_a_new_member_is_not_added_to_the_daily(sprints):
    saved = (await sprints.start(_body(sprints.dora, sprints.ana))).json()
    await sprints.world.admin_invites(sprints.team.id, sprints.ana.id, email="elena@example.test")

    elena = await sprints.world.activate.handle(ActivateAccount(token=TOKEN, password=PASSWORD))

    assert elena.team_id == sprints.team.id
    assert await sprints.world.team_queries.membership_of(
        team_id=sprints.team.id, user_id=elena.user_id
    )
    assert await sprints.active() == saved


# ----------------------------------------------------------- authorization --
async def test_a_member_cannot_start_or_edit_the_sprint_but_can_read_its_day(sprints, engine):
    refused_start = await sprints.start(_body(sprints.bruno), TOKEN_BRUNO)
    saved = (await sprints.start(_body(sprints.ana, sprints.bruno))).json()
    refused_edit = await sprints.edit(_body(sprints.bruno), TOKEN_BRUNO)
    read = await sprints.read(TOKEN_BRUNO)

    for refused in (refused_start, refused_edit):
        assert refused.status_code == 403
        assert refused.json()["error"]["code"] == "not_a_team_admin"
    assert read.status_code == 200
    assert read.json() == saved
    assert read.json()["day"] == {"number": 0, "total": 12, "phase": "not_started"}
    assert await _stored_turns(engine, sprints.team.id) == [
        (str(sprints.ana.id), 1),
        (str(sprints.bruno.id), 2),
    ]


ROUTES = [
    ("POST", "/sprints", {"json": _body()}),
    ("GET", "/sprints/active", {}),
    ("PUT", "/sprints/active", {"json": _body()}),
]


@pytest.mark.parametrize(("method", "path", "kwargs"), ROUTES)
async def test_someone_outside_the_team_cannot_reach_its_sprint(
    sprints, engine, method, path, kwargs
):
    saved = (await sprints.start(_body(sprints.ana))).json()

    response = await sprints.request(method, path, TOKEN_CARLA, **kwargs)

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "not_a_team_member"
    assert str(sprints.ana.id) not in response.text
    assert await sprints.active() == saved
