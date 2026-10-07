"""StartSprint against a real PostgreSQL: the sprint and its participants are stored in one
transaction, and the read side returns it with its day N of M and next daily (HU-07)."""

import pytest

from agilina_api.teams.application.queries.get_active_sprint import GetActiveSprint
from agilina_shared.sprint_calendar import SprintDay, SprintPhase
from tests.api.builders import DAILY_TIME, StartSprintBuilder, TeamBuilder
from tests.api.integration.support import stored_team, stored_user
from tests.api.integration.world import World

pytestmark = pytest.mark.integration


async def test_a_started_sprint_is_read_back_with_its_day_and_next_daily(session_factory):
    world = World(session_factory)
    ana, bruno = await stored_user(session_factory), await stored_user(session_factory)
    team = await stored_team(
        session_factory, TeamBuilder().with_admin(ana.id).with_member(bruno.id)
    )

    sprint_id = await world.start_sprint.handle(
        StartSprintBuilder().for_team(team.id).with_participants(bruno.id, ana.id).build()
    )
    view = await world.active_sprint.handle(GetActiveSprint(team_id=team.id))

    assert view is not None
    assert view.sprint.sprint_id == sprint_id
    assert view.sprint.participants == (bruno.id, ana.id)
    assert view.day == SprintDay(number=0, total=12, phase=SprintPhase.NOT_STARTED)
    assert view.next_daily_at == DAILY_TIME
