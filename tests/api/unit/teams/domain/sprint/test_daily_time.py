"""The daily's time: a UTC anchor instant plus the time zone it was captured in (AD-31)."""

from datetime import UTC, datetime, time, timedelta, timezone, tzinfo
from zoneinfo import ZoneInfo

import pytest

from agilina_api.teams.domain.sprint import DailyTime


class _NoOffset(tzinfo):
    """A time zone that knows no offset: a datetime with it is still not an instant."""

    def utcoffset(self, dt: datetime | None) -> timedelta | None:
        return None


def test_the_anchor_is_kept_in_utc_whatever_offset_it_came_with():
    bogota = timezone(timedelta(hours=-5))

    daily = DailyTime(at=datetime(2026, 10, 5, 9, 0, tzinfo=bogota), time_zone="America/Bogota")

    assert daily.at == datetime(2026, 10, 5, 14, 0, tzinfo=UTC)
    assert daily.at.tzinfo is UTC


def test_the_wall_clock_time_is_the_anchor_seen_in_the_capture_time_zone():
    daily = DailyTime(at=datetime(2026, 10, 5, 13, 0, tzinfo=UTC), time_zone="America/New_York")

    assert daily.local_time == time(9, 0)
    assert daily.local_time.tzinfo is None
    assert daily.zone == ZoneInfo("America/New_York")


def test_an_early_daily_east_of_utc_keeps_its_wall_clock_time():
    """08:00 in Tokyo is 23:00 UTC of the day before: the wall-clock time is still 08:00."""
    daily = DailyTime(at=datetime(2026, 10, 4, 23, 0, tzinfo=UTC), time_zone="Asia/Tokyo")

    assert daily.local_time == time(8, 0)


@pytest.mark.parametrize(
    "at", [datetime(2026, 10, 5, 9, 0), datetime(2026, 10, 5, 9, 0, tzinfo=_NoOffset())]
)
def test_a_time_without_an_offset_is_not_an_instant_and_is_refused(at):
    with pytest.raises(ValueError, match="aware"):
        DailyTime(at=at, time_zone="America/Bogota")


def test_two_daily_times_at_the_same_instant_and_zone_are_equal():
    utc = DailyTime(at=datetime(2026, 10, 5, 14, 0, tzinfo=UTC), time_zone="America/Bogota")
    local = DailyTime(
        at=datetime(2026, 10, 5, 9, 0, tzinfo=ZoneInfo("America/Bogota")),
        time_zone="America/Bogota",
    )

    assert utc == local
