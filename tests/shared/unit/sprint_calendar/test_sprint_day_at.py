"""Day N of M of the sprint: every calendar day counts, weekends included, and today is the date
in the daily's capture time zone, not in UTC (AD-31)."""

from datetime import UTC, date, datetime, timedelta, timezone, tzinfo
from zoneinfo import ZoneInfo

import pytest

from agilina_shared.sprint_calendar import SprintDay, SprintPhase, sprint_day_at

# The reference sprint: Monday 2026-10-05 to Friday 2026-10-16, twelve calendar days.
START = date(2026, 10, 5)
END = date(2026, 10, 16)
BOGOTA = ZoneInfo("America/Bogota")  # UTC-5 all year: local noon is 17:00Z
TOKYO = ZoneInfo("Asia/Tokyo")  # UTC+9 all year


class _ZoneWithoutOffset(tzinfo):
    """A tzinfo that does not know its offset: the datetime it carries is still naive."""

    def utcoffset(self, dt: datetime | None) -> timedelta | None:
        return None


@pytest.mark.parametrize(
    ("now", "expected"),
    [
        pytest.param(
            datetime(2026, 10, 5, 17, tzinfo=UTC),
            SprintDay(number=1, total=12, phase=SprintPhase.IN_PROGRESS),
            id="first-day",
        ),
        pytest.param(
            datetime(2026, 10, 7, 17, tzinfo=UTC),
            SprintDay(number=3, total=12, phase=SprintPhase.IN_PROGRESS),
            id="wednesday",
        ),
        pytest.param(
            datetime(2026, 10, 10, 17, tzinfo=UTC),
            SprintDay(number=6, total=12, phase=SprintPhase.IN_PROGRESS),
            id="saturday-counts",
        ),
        pytest.param(
            datetime(2026, 10, 11, 17, tzinfo=UTC),
            SprintDay(number=7, total=12, phase=SprintPhase.IN_PROGRESS),
            id="sunday-counts",
        ),
        pytest.param(
            datetime(2026, 10, 16, 17, tzinfo=UTC),
            SprintDay(number=12, total=12, phase=SprintPhase.IN_PROGRESS),
            id="last-day",
        ),
        pytest.param(
            datetime(2026, 10, 4, 17, tzinfo=UTC),
            SprintDay(number=0, total=12, phase=SprintPhase.NOT_STARTED),
            id="day-before-start",
        ),
        pytest.param(
            datetime(2026, 9, 1, 17, tzinfo=UTC),
            SprintDay(number=0, total=12, phase=SprintPhase.NOT_STARTED),
            id="long-before-start",
        ),
        pytest.param(
            datetime(2026, 10, 17, 17, tzinfo=UTC),
            SprintDay(number=12, total=12, phase=SprintPhase.FINISHED),
            id="day-after-end",
        ),
        pytest.param(
            datetime(2026, 12, 1, 17, tzinfo=UTC),
            SprintDay(number=12, total=12, phase=SprintPhase.FINISHED),
            id="long-after-end",
        ),
    ],
)
def test_the_sprint_day_counts_every_calendar_day_of_the_period(now: datetime, expected: SprintDay):
    assert sprint_day_at(start=START, end=END, time_zone=BOGOTA, now=now) == expected


def test_in_tokyo_the_first_day_starts_while_it_is_still_sunday_in_utc():
    now = datetime(2026, 10, 4, 23, 30, tzinfo=UTC)  # Monday 08:30 in Tokyo

    day = sprint_day_at(start=START, end=END, time_zone=TOKYO, now=now)

    assert day == SprintDay(number=1, total=12, phase=SprintPhase.IN_PROGRESS)


def test_a_utc_instant_that_is_still_the_previous_day_locally_gives_the_previous_day():
    now = datetime(2026, 10, 7, 3, 0, tzinfo=UTC)  # Tuesday 22:00 in Bogotá, Wednesday in UTC

    day = sprint_day_at(start=START, end=END, time_zone=BOGOTA, now=now)

    assert day == SprintDay(number=2, total=12, phase=SprintPhase.IN_PROGRESS)


@pytest.mark.parametrize(
    ("now", "expected"),
    [
        pytest.param(
            datetime(2026, 10, 4, 14, 59, 59, tzinfo=UTC),
            SprintDay(number=0, total=12, phase=SprintPhase.NOT_STARTED),
            id="last-second-before-local-midnight-of-the-start",
        ),
        pytest.param(
            datetime(2026, 10, 4, 15, 0, tzinfo=UTC),
            SprintDay(number=1, total=12, phase=SprintPhase.IN_PROGRESS),
            id="local-midnight-of-the-start",
        ),
        pytest.param(
            datetime(2026, 10, 16, 14, 59, 59, tzinfo=UTC),
            SprintDay(number=12, total=12, phase=SprintPhase.IN_PROGRESS),
            id="last-second-of-the-end",
        ),
        pytest.param(
            datetime(2026, 10, 16, 15, 0, tzinfo=UTC),
            SprintDay(number=12, total=12, phase=SprintPhase.FINISHED),
            id="local-midnight-after-the-end",
        ),
    ],
)
def test_the_day_changes_at_local_midnight_of_the_capture_zone(now: datetime, expected: SprintDay):
    assert sprint_day_at(start=START, end=END, time_zone=TOKYO, now=now) == expected


def test_the_same_instant_gives_the_same_day_whatever_offset_it_is_expressed_in():
    in_utc = datetime(2026, 10, 7, 3, 0, tzinfo=UTC)
    in_tokyo_offset = in_utc.astimezone(timezone(timedelta(hours=9)))

    assert sprint_day_at(start=START, end=END, time_zone=BOGOTA, now=in_tokyo_offset) == (
        sprint_day_at(start=START, end=END, time_zone=BOGOTA, now=in_utc)
    )


def test_a_sprint_may_start_on_saturday_and_end_on_sunday():
    saturday = date(2026, 10, 10)
    next_sunday = date(2026, 10, 18)

    first = sprint_day_at(
        start=saturday,
        end=next_sunday,
        time_zone=BOGOTA,
        now=datetime(2026, 10, 10, 17, tzinfo=UTC),
    )
    last = sprint_day_at(
        start=saturday,
        end=next_sunday,
        time_zone=BOGOTA,
        now=datetime(2026, 10, 18, 17, tzinfo=UTC),
    )

    assert first == SprintDay(number=1, total=9, phase=SprintPhase.IN_PROGRESS)
    assert last == SprintDay(number=9, total=9, phase=SprintPhase.IN_PROGRESS)


def test_a_one_day_sprint_is_day_one_of_one():
    day = sprint_day_at(
        start=date(2026, 10, 7),
        end=date(2026, 10, 7),
        time_zone=BOGOTA,
        now=datetime(2026, 10, 7, 17, tzinfo=UTC),
    )

    assert day == SprintDay(number=1, total=1, phase=SprintPhase.IN_PROGRESS)


def test_a_naive_instant_is_rejected():
    with pytest.raises(ValueError, match="aware"):
        sprint_day_at(start=START, end=END, time_zone=BOGOTA, now=datetime(2026, 10, 7, 12))


def test_an_instant_whose_zone_has_no_offset_is_rejected():
    now = datetime(2026, 10, 7, 12, tzinfo=_ZoneWithoutOffset())

    with pytest.raises(ValueError, match="aware"):
        sprint_day_at(start=START, end=END, time_zone=BOGOTA, now=now)


def test_a_period_that_ends_before_it_starts_is_rejected():
    with pytest.raises(ValueError, match="before start"):
        sprint_day_at(
            start=END, end=START, time_zone=BOGOTA, now=datetime(2026, 10, 7, 17, tzinfo=UTC)
        )
