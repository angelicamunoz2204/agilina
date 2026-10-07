"""The ``Sprint`` aggregate: it starts active, keeps its participants in turn order and can be
reconfigured whole (HU-07)."""

from datetime import UTC, date, datetime

from agilina_api.teams.domain.sprint import DailyTime, Sprint, SprintPeriod, SprintStatus
from tests.api.builders import SprintBuilder, next_id


def test_a_started_sprint_is_active_with_its_period_daily_time_and_team():
    sprint_id, team_id = next_id(), next_id()
    period = SprintPeriod(start=date(2026, 10, 5), end=date(2026, 10, 16))
    daily = DailyTime(at=datetime(2026, 10, 5, 14, 0, tzinfo=UTC), time_zone="America/Bogota")

    sprint = Sprint.start(
        sprint_id=sprint_id, team_id=team_id, period=period, daily_time=daily, participants=[]
    )

    assert sprint.id == sprint_id and sprint.team_id == team_id
    assert sprint.status is SprintStatus.ACTIVE
    assert sprint.period == period and sprint.daily_time == daily
    assert sprint.participants == ()


def test_the_participants_keep_the_order_they_were_given_which_is_the_turn_order():
    ana, bruno, carla = next_id(), next_id(), next_id()

    sprint = SprintBuilder().with_participants(carla, ana, bruno).build()

    assert sprint.participants == (carla, ana, bruno)


def test_the_sprint_keeps_its_own_copy_of_the_participants():
    ana, bruno = next_id(), next_id()
    given = [ana, bruno]

    sprint = Sprint.start(
        sprint_id=next_id(),
        team_id=next_id(),
        period=SprintPeriod(start=date(2026, 10, 5), end=date(2026, 10, 16)),
        daily_time=DailyTime(
            at=datetime(2026, 10, 5, 14, 0, tzinfo=UTC), time_zone="America/Bogota"
        ),
        participants=given,
    )
    given.reverse()

    assert sprint.participants == (ana, bruno)


def test_reconfiguring_replaces_the_period_the_daily_time_its_zone_and_the_order():
    ana, bruno, carla = next_id(), next_id(), next_id()
    sprint = SprintBuilder().with_participants(ana, bruno).build()
    period = SprintPeriod(start=date(2026, 10, 10), end=date(2026, 10, 24))
    tokyo = DailyTime(at=datetime(2026, 10, 9, 23, 0, tzinfo=UTC), time_zone="Asia/Tokyo")

    sprint.reconfigure(period=period, daily_time=tokyo, participants=[bruno, carla, ana])

    assert sprint.period == period
    assert sprint.daily_time == tokyo and sprint.daily_time.time_zone == "Asia/Tokyo"
    assert sprint.participants == (bruno, carla, ana)


def test_reconfiguring_does_not_change_the_status():
    active = SprintBuilder().build()
    closed = SprintBuilder().closed().build()
    period = SprintPeriod(start=date(2026, 10, 12), end=date(2026, 10, 23))

    for sprint in (active, closed):
        sprint.reconfigure(period=period, daily_time=sprint.daily_time, participants=())

    assert active.status is SprintStatus.ACTIVE and closed.status is SprintStatus.CLOSED


def test_a_stored_sprint_is_restored_with_the_status_it_was_saved_with():
    planned = SprintBuilder().planned().build()

    assert planned.status is SprintStatus.PLANNED
