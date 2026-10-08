"""The calendar dates of a sprint: any day of the week, both ends included, and the end never
before the start (HU-07)."""

import dataclasses
from datetime import date

import pytest

from agilina_api.teams.domain.errors import SprintEndsBeforeStartError
from agilina_api.teams.domain.sprint import SprintPeriod


def test_a_period_holds_its_two_calendar_dates():
    period = SprintPeriod(start=date(2026, 10, 5), end=date(2026, 10, 16))

    assert (period.start, period.end) == (date(2026, 10, 5), date(2026, 10, 16))


def test_a_period_may_start_and_end_on_a_weekend_and_last_a_single_day():
    """Every calendar day counts (AD-31): a Saturday-to-Sunday or a one-day sprint is fine."""
    weekend = SprintPeriod(start=date(2026, 10, 10), end=date(2026, 10, 11))
    one_day = SprintPeriod(start=date(2026, 10, 11), end=date(2026, 10, 11))

    assert weekend.start.weekday() == 5 and weekend.end.weekday() == 6
    assert one_day.start == one_day.end


def test_a_period_may_last_a_single_weekday():
    wednesday = date(2026, 10, 7)

    period = SprintPeriod(start=wednesday, end=wednesday)

    assert period.start == period.end and wednesday.weekday() == 2


@pytest.mark.parametrize(
    ("start", "end"),
    [
        (date(2026, 10, 16), date(2026, 10, 5)),
        (date(2026, 10, 6), date(2026, 10, 5)),  # one day before is already before
        (date(2027, 1, 1), date(2026, 12, 31)),
    ],
)
def test_a_period_that_ends_before_it_starts_is_refused(start, end):
    with pytest.raises(SprintEndsBeforeStartError) as refused:
        SprintPeriod(start=start, end=end)

    # The message is generic: it does not repeat the dates that were sent.
    assert str(start) not in str(refused.value) and str(end) not in str(refused.value)


def test_a_period_is_a_value():
    period = SprintPeriod(start=date(2026, 10, 5), end=date(2026, 10, 16))

    assert period == SprintPeriod(start=date(2026, 10, 5), end=date(2026, 10, 16))
    with pytest.raises(dataclasses.FrozenInstanceError):
        period.start = date(2026, 10, 6)  # type: ignore[misc]
