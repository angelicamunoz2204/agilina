"""The daily happens at the same wall-clock time of the capture time zone on every calendar day
of the sprint, weekends included, and is stored as UTC instants (AD-31)."""

from datetime import UTC, date, datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo

from agilina_shared.sprint_calendar import daily_occurrences

NEW_YORK = ZoneInfo("America/New_York")
TOKYO = ZoneInfo("Asia/Tokyo")


def test_new_york_keeps_the_wall_clock_time_across_the_march_change():
    occurrences = daily_occurrences(
        start=date(2027, 3, 8), end=date(2027, 3, 19), local_time=time(9), time_zone=NEW_YORK
    )

    by_date = {occurrence.astimezone(NEW_YORK).date(): occurrence for occurrence in occurrences}
    assert by_date[date(2027, 3, 12)] == datetime(2027, 3, 12, 14, 0, tzinfo=UTC)
    assert by_date[date(2027, 3, 13)] == datetime(2027, 3, 13, 14, 0, tzinfo=UTC)
    assert by_date[date(2027, 3, 14)] == datetime(2027, 3, 14, 13, 0, tzinfo=UTC)
    assert by_date[date(2027, 3, 15)] == datetime(2027, 3, 15, 13, 0, tzinfo=UTC)
    assert all(occurrence.astimezone(NEW_YORK).time() == time(9) for occurrence in occurrences)


def test_an_early_daily_in_tokyo_falls_on_the_same_tokyo_date_every_day_including_the_weekend():
    start = date(2026, 10, 5)  # Monday
    end = date(2026, 10, 11)  # Sunday

    occurrences = daily_occurrences(start=start, end=end, local_time=time(8), time_zone=TOKYO)

    assert occurrences == tuple(
        datetime(2026, 10, 4, 23, 0, tzinfo=UTC) + timedelta(days=offset) for offset in range(7)
    )
    assert [occurrence.astimezone(TOKYO).date() for occurrence in occurrences] == [
        start + timedelta(days=offset) for offset in range(7)
    ]
    assert [occurrence.astimezone(TOKYO).isoweekday() for occurrence in occurrences] == [
        1,
        2,
        3,
        4,
        5,
        6,
        7,
    ]


def test_every_calendar_day_of_the_period_has_one_occurrence_in_chronological_order():
    occurrences = daily_occurrences(
        start=date(2026, 10, 5), end=date(2026, 10, 16), local_time=time(9, 15), time_zone=TOKYO
    )

    assert len(occurrences) == 12
    assert list(occurrences) == sorted(occurrences)
    assert all(occurrence.tzinfo is UTC for occurrence in occurrences)


def test_a_sprint_may_start_on_saturday_and_end_on_sunday():
    occurrences = daily_occurrences(
        start=date(2026, 10, 10), end=date(2026, 10, 18), local_time=time(9), time_zone=NEW_YORK
    )

    local_dates = [occurrence.astimezone(NEW_YORK).date() for occurrence in occurrences]
    assert local_dates[0] == date(2026, 10, 10)
    assert local_dates[-1] == date(2026, 10, 18)
    assert len(local_dates) == 9


def test_a_one_day_sprint_has_a_single_occurrence():
    occurrences = daily_occurrences(
        start=date(2026, 10, 7), end=date(2026, 10, 7), local_time=time(9), time_zone=NEW_YORK
    )

    assert occurrences == (datetime(2026, 10, 7, 13, 0, tzinfo=UTC),)


def test_a_period_that_ends_before_it_starts_has_no_occurrences():
    occurrences = daily_occurrences(
        start=date(2026, 10, 16), end=date(2026, 10, 5), local_time=time(9), time_zone=NEW_YORK
    )

    assert occurrences == ()


def test_a_wall_clock_time_skipped_by_the_spring_change_resolves_with_fold_zero():
    occurrences = daily_occurrences(
        start=date(2027, 3, 14), end=date(2027, 3, 14), local_time=time(2, 30), time_zone=NEW_YORK
    )

    assert occurrences == (datetime(2027, 3, 14, 7, 30, tzinfo=UTC),)


def test_a_wall_clock_time_repeated_by_the_autumn_change_resolves_with_fold_zero():
    occurrences = daily_occurrences(
        start=date(2027, 11, 7), end=date(2027, 11, 7), local_time=time(1, 30), time_zone=NEW_YORK
    )

    assert occurrences == (datetime(2027, 11, 7, 5, 30, tzinfo=UTC),)


def test_the_fold_carried_by_the_local_time_is_ignored():
    occurrences = daily_occurrences(
        start=date(2027, 11, 7),
        end=date(2027, 11, 7),
        local_time=time(1, 30, fold=1),
        time_zone=NEW_YORK,
    )

    assert occurrences == (datetime(2027, 11, 7, 5, 30, tzinfo=UTC),)


def test_the_time_zone_carried_by_the_local_time_is_ignored_in_favour_of_the_capture_zone():
    occurrences = daily_occurrences(
        start=date(2026, 10, 7),
        end=date(2026, 10, 7),
        local_time=time(9, tzinfo=timezone(timedelta(hours=-5))),
        time_zone=TOKYO,
    )

    assert occurrences == (datetime(2026, 10, 7, 0, 0, tzinfo=UTC),)
