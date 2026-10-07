"""ReconfigureSprint against a real PostgreSQL: the active sprint is edited in place, as many
times as the admin saves, and the read side always sees the last version (HU-07)."""

from datetime import UTC, datetime

import pytest

from agilina_api.teams.application.queries.get_active_sprint import GetActiveSprint
from agilina_api.teams.domain.errors import NoActiveSprintError
from tests.api.builders import ReconfigureSprintBuilder, SprintBuilder, TeamBuilder
from tests.api.integration.support import stored_sprint, stored_team, stored_user
from tests.api.integration.world import World

pytestmark = pytest.mark.integration


async def test_editing_twice_in_a_row_reorders_the_daily_and_moves_its_time(session_factory):
    world = World(session_factory)
    ana, bruno, carla = [await stored_user(session_factory) for _ in range(3)]
    team = await stored_team(
        session_factory,
        TeamBuilder().with_admin(ana.id).with_member(bruno.id).with_member(carla.id),
    )
    sprint = await stored_sprint(session_factory, SprintBuilder().for_team(team))
    edit = ReconfigureSprintBuilder().for_team(team.id)

    await world.reconfigure_sprint.handle(
        edit.with_participants(carla.id, bruno.id, ana.id).build()
    )
    await world.reconfigure_sprint.handle(
        edit.with_daily_time(datetime(2026, 10, 4, 23, 0, tzinfo=UTC), "Asia/Tokyo")
        .with_participants(bruno.id, carla.id)
        .build()
    )
    view = await world.active_sprint.handle(GetActiveSprint(team_id=team.id))

    assert view is not None and view.sprint.sprint_id == sprint.id
    assert view.sprint.participants == (bruno.id, carla.id)
    assert view.sprint.time_zone == "Asia/Tokyo"
    assert view.next_daily_at == datetime(2026, 10, 4, 23, 0, tzinfo=UTC)


async def test_a_team_without_an_active_sprint_has_nothing_to_edit(session_factory):
    world = World(session_factory)
    team = await stored_team(session_factory)
    await stored_sprint(session_factory, SprintBuilder().for_team(team).closed())

    with pytest.raises(NoActiveSprintError):
        await world.reconfigure_sprint.handle(ReconfigureSprintBuilder().for_team(team.id).build())
