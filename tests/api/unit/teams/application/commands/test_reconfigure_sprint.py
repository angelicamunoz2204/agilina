"""ReconfigureSprint: an admin edits the team's active sprint whole, with the same rules as
when it starts; without one there is nothing to edit (HU-07)."""

import logging
from datetime import UTC, date, datetime

import pytest

from agilina_api.teams.application.commands.reconfigure_sprint import ReconfigureSprintHandler
from agilina_api.teams.domain.errors import (
    DailyParticipantNotAMemberError,
    DuplicateDailyParticipantError,
    InvalidTimeZoneError,
    NoActiveSprintError,
    NoDailyParticipantsError,
    SprintEndsBeforeStartError,
    TeamNotFoundError,
)
from agilina_api.teams.domain.sprint import DailyTime, SprintPeriod, SprintStatus
from tests.api.builders import ReconfigureSprintBuilder, SprintBuilder, TeamBuilder, next_id
from tests.api.doubles import FakeTeamsUnitOfWork


class Scenario:
    """Atlas, administered by Ana, with Bruno and Carla as members."""

    def __init__(self) -> None:
        self.ana, self.bruno, self.carla = next_id(), next_id(), next_id()
        self.uow = FakeTeamsUnitOfWork()
        self.handler = ReconfigureSprintHandler(lambda: self.uow)

    async def a_team(self, builder: TeamBuilder | None = None):
        team = builder or (
            TeamBuilder().with_admin(self.ana).with_member(self.bruno).with_member(self.carla)
        )
        return await team.saved_in(self.uow.teams)

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


# ----------------------------------------------------------------- the rules --
@pytest.mark.parametrize(
    ("edit", "error"),
    [
        (
            lambda b, s: b.with_period(date(2026, 10, 16), date(2026, 10, 15)),
            SprintEndsBeforeStartError,
        ),
        (
            lambda b, s: b.with_daily_time(datetime(2026, 10, 5, 14, 0, tzinfo=UTC), "utc"),
            InvalidTimeZoneError,
        ),
        (lambda b, s: b.with_participants(), NoDailyParticipantsError),
        (lambda b, s: b.with_participants(s.bruno, s.bruno), DuplicateDailyParticipantError),
        (lambda b, s: b.with_participants(s.ana, next_id()), DailyParticipantNotAMemberError),
    ],
    ids=["ends_before_start", "time_zone", "no_participants", "twice", "outsider"],
)
async def test_an_edit_that_breaks_a_rule_changes_nothing(scenario, edit, error):
    team = await scenario.a_team()
    sprint = await scenario.a_sprint(SprintBuilder().for_team(team))
    valid = ReconfigureSprintBuilder().for_team(team.id).with_participants(scenario.ana)

    with pytest.raises(error):
        await scenario.handler.handle(edit(valid, scenario).build())

    stored = scenario.uow.sprints.sprints[sprint.id]
    assert (stored.period, stored.daily_time, stored.participants) == (
        sprint.period,
        sprint.daily_time,
        sprint.participants,
    )
    assert scenario.uow.sprints.saved == [] and scenario.uow.committed is False


async def test_a_member_who_was_removed_cannot_be_kept_in_the_daily(scenario):
    team = await scenario.a_team(
        TeamBuilder().with_admin(scenario.ana).with_removed_member(scenario.bruno)
    )
    sprint = await scenario.a_sprint(
        SprintBuilder().for_team_id(team.id).with_participants(scenario.ana)
    )

    with pytest.raises(DailyParticipantNotAMemberError):
        await scenario.handler.handle(
            ReconfigureSprintBuilder()
            .for_team(team.id)
            .with_participants(scenario.bruno, scenario.ana)
            .build()
        )

    assert scenario.uow.sprints.sprints[sprint.id].participants == (scenario.ana,)
    assert scenario.uow.committed is False


async def test_a_sprint_left_without_participants_is_configured_again_with_active_members(
    scenario,
):
    """A removal may leave the daily empty (Q4); the next edit gives it its participants."""
    team = await scenario.a_team()
    sprint = await scenario.a_sprint(SprintBuilder().for_team_id(team.id))

    await scenario.handler.handle(
        ReconfigureSprintBuilder()
        .for_team(team.id)
        .with_participants(scenario.carla, scenario.bruno)
        .build()
    )

    assert scenario.uow.sprints.sprints[sprint.id].participants == (scenario.carla, scenario.bruno)


# ------------------------------------------------------------------- the log --
async def test_an_edit_is_logged_with_who_asked_and_the_sprint(scenario, caplog):
    team = await scenario.a_team()
    sprint = await scenario.a_sprint(SprintBuilder().for_team(team))

    with caplog.at_level(logging.INFO):
        await scenario.handler.handle(
            ReconfigureSprintBuilder()
            .for_team(team.id)
            .with_participants(scenario.carla)
            .requested_by_admin(scenario.ana)
            .build()
        )

    assert f"Team {team.id}: user {scenario.ana} reconfigured sprint {sprint.id}" in caplog.text
    assert str(scenario.carla) not in caplog.text


async def test_a_refused_edit_logs_nothing(scenario, caplog):
    team = await scenario.a_team()
    await scenario.a_sprint(SprintBuilder().for_team(team))

    with caplog.at_level(logging.INFO), pytest.raises(NoDailyParticipantsError):
        await scenario.handler.handle(ReconfigureSprintBuilder().for_team(team.id).build())

    assert "reconfigured sprint" not in caplog.text
