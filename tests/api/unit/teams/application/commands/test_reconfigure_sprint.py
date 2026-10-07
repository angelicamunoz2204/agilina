"""ReconfigureSprint: an admin edits the team's active sprint whole; without one there is
nothing to edit (HU-07)."""

from datetime import UTC, date, datetime

import pytest

from agilina_api.teams.application.commands.reconfigure_sprint import ReconfigureSprintHandler
from agilina_api.teams.domain.errors import NoActiveSprintError, TeamNotFoundError
from agilina_api.teams.domain.sprint import DailyTime, SprintPeriod, SprintStatus
from tests.api.builders import ReconfigureSprintBuilder, SprintBuilder, TeamBuilder, next_id
from tests.api.doubles import FakeTeamsUnitOfWork


class Scenario:
    """Atlas, administered by Ana, with Bruno and Carla as members."""

    def __init__(self) -> None:
        self.ana, self.bruno, self.carla = next_id(), next_id(), next_id()
        self.uow = FakeTeamsUnitOfWork()
        self.handler = ReconfigureSprintHandler(lambda: self.uow)

    async def a_team(self):
        return await (
            TeamBuilder()
            .with_admin(self.ana)
            .with_member(self.bruno)
            .with_member(self.carla)
            .saved_in(self.uow.teams)
        )

    async def a_sprint(self, builder: SprintBuilder):
        return await builder.saved_in(self.uow.sprints)


@pytest.fixture
def scenario() -> Scenario:
    return Scenario()


async def test_editing_replaces_the_period_the_daily_time_and_the_turn_order(scenario):
    team = await scenario.a_team()
    sprint = await scenario.a_sprint(SprintBuilder().for_team(team))
    tokyo = datetime(2026, 10, 11, 23, 0, tzinfo=UTC)

    await scenario.handler.handle(
        ReconfigureSprintBuilder()
        .for_team(team.id)
        .with_period(date(2026, 10, 12), date(2026, 10, 23))
        .with_daily_time(tokyo, "Asia/Tokyo")
        .with_participants(scenario.carla, scenario.ana)
        .build()
    )

    edited = scenario.uow.sprints.sprints[sprint.id]
    assert edited.period == SprintPeriod(start=date(2026, 10, 12), end=date(2026, 10, 23))
    assert edited.daily_time == DailyTime(at=tokyo, time_zone="Asia/Tokyo")
    assert edited.participants == (scenario.carla, scenario.ana)
    assert edited.status is SprintStatus.ACTIVE
    assert scenario.uow.sprints.saved == [sprint.id] and scenario.uow.committed is True


async def test_only_the_active_sprint_is_edited(scenario):
    team = await scenario.a_team()
    closed = await scenario.a_sprint(SprintBuilder().for_team(team).closed())
    active = await scenario.a_sprint(SprintBuilder().for_team(team))

    await scenario.handler.handle(
        ReconfigureSprintBuilder().for_team(team.id).with_participants(scenario.bruno).build()
    )

    assert scenario.uow.sprints.sprints[active.id].participants == (scenario.bruno,)
    assert scenario.uow.sprints.sprints[closed.id].participants == closed.participants


async def test_without_an_active_sprint_there_is_nothing_to_edit_and_nothing_is_saved(scenario):
    team = await scenario.a_team()
    closed = await scenario.a_sprint(SprintBuilder().for_team(team).closed())
    await scenario.a_sprint(SprintBuilder().for_team_id(next_id()))  # another team's

    with pytest.raises(NoActiveSprintError):
        await scenario.handler.handle(ReconfigureSprintBuilder().for_team(team.id).build())

    assert scenario.uow.sprints.saved == [] and scenario.uow.committed is False
    assert scenario.uow.sprints.sprints[closed.id].status is SprintStatus.CLOSED


async def test_a_team_that_does_not_exist_has_no_sprint_to_edit(scenario):
    with pytest.raises(TeamNotFoundError):
        await scenario.handler.handle(ReconfigureSprintBuilder().for_team(next_id()).build())

    assert scenario.uow.sprints.saved == [] and scenario.uow.committed is False


async def test_a_daily_time_without_an_offset_changes_nothing(scenario):
    team = await scenario.a_team()
    sprint = await scenario.a_sprint(SprintBuilder().for_team(team))

    with pytest.raises(ValueError, match="aware"):
        await scenario.handler.handle(
            ReconfigureSprintBuilder()
            .for_team(team.id)
            .with_daily_time(datetime(2026, 10, 5, 9, 0), "America/Bogota")
            .build()
        )

    assert scenario.uow.sprints.sprints[sprint.id].daily_time == sprint.daily_time
    assert scenario.uow.sprints.saved == [] and scenario.uow.committed is False
