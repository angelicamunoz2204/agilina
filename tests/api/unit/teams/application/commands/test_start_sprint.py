"""StartSprint: an admin configures the team's sprint, which is stored active with the daily's
time in UTC, its capture time zone and the participants in turn order (HU-07)."""

from datetime import UTC, date, datetime, timedelta, timezone

import pytest

from agilina_api.teams.application.commands.start_sprint import StartSprintHandler
from agilina_api.teams.domain.errors import TeamNotFoundError
from agilina_api.teams.domain.sprint import DailyTime, SprintPeriod, SprintStatus
from tests.api.builders import StartSprintBuilder, TeamBuilder, next_id
from tests.api.doubles import FakeTeamsUnitOfWork


class Scenario:
    """Atlas, administered by Ana, with Bruno and Carla as members."""

    def __init__(self) -> None:
        self.ana, self.bruno, self.carla = next_id(), next_id(), next_id()
        self.uow = FakeTeamsUnitOfWork()
        self.handler = StartSprintHandler(lambda: self.uow, new_id=next_id)

    async def a_team(self):
        return await (
            TeamBuilder()
            .with_admin(self.ana)
            .with_member(self.bruno)
            .with_member(self.carla)
            .saved_in(self.uow.teams)
        )


@pytest.fixture
def scenario() -> Scenario:
    return Scenario()


async def test_starting_a_sprint_stores_it_active_and_returns_its_id(scenario):
    team = await scenario.a_team()

    sprint_id = await scenario.handler.handle(
        StartSprintBuilder()
        .for_team(team.id)
        .with_period(date(2026, 10, 5), date(2026, 10, 16))
        .with_participants(scenario.carla, scenario.ana)
        .build()
    )

    stored = scenario.uow.sprints.sprints[sprint_id]
    assert stored.team_id == team.id and stored.status is SprintStatus.ACTIVE
    assert stored.period == SprintPeriod(start=date(2026, 10, 5), end=date(2026, 10, 16))
    assert stored.participants == (scenario.carla, scenario.ana)
    assert scenario.uow.committed is True


async def test_the_daily_time_is_stored_in_utc_with_the_time_zone_it_was_captured_in(scenario):
    team = await scenario.a_team()
    nine_in_bogota = datetime(2026, 10, 5, 9, 0, tzinfo=timezone(timedelta(hours=-5)))

    sprint_id = await scenario.handler.handle(
        StartSprintBuilder()
        .for_team(team.id)
        .with_daily_time(nine_in_bogota, "America/Bogota")
        .build()
    )

    daily = scenario.uow.sprints.sprints[sprint_id].daily_time
    assert daily == DailyTime(
        at=datetime(2026, 10, 5, 14, 0, tzinfo=UTC), time_zone="America/Bogota"
    )
    assert daily.at.tzinfo is UTC


async def test_each_sprint_gets_a_new_id(scenario):
    first_team, second_team = await scenario.a_team(), await scenario.a_team()

    first = await scenario.handler.handle(StartSprintBuilder().for_team(first_team.id).build())
    second = await scenario.handler.handle(StartSprintBuilder().for_team(second_team.id).build())

    assert first != second
    assert set(scenario.uow.sprints.sprints) == {first, second}


async def test_a_team_that_does_not_exist_gets_no_sprint(scenario):
    with pytest.raises(TeamNotFoundError):
        await scenario.handler.handle(StartSprintBuilder().for_team(next_id()).build())

    assert scenario.uow.sprints.sprints == {} and scenario.uow.committed is False


async def test_a_daily_time_without_an_offset_stores_nothing(scenario):
    team = await scenario.a_team()

    with pytest.raises(ValueError, match="aware"):
        await scenario.handler.handle(
            StartSprintBuilder()
            .for_team(team.id)
            .with_daily_time(datetime(2026, 10, 5, 9, 0), "America/Bogota")
            .build()
        )

    assert scenario.uow.sprints.sprints == {} and scenario.uow.committed is False
