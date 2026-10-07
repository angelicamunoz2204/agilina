"""The calendar dates of a sprint: any day of the week, both ends included."""

import dataclasses
from datetime import date

import pytest

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


def test_a_period_is_a_value():
    period = SprintPeriod(start=date(2026, 10, 5), end=date(2026, 10, 16))

    assert period == SprintPeriod(start=date(2026, 10, 5), end=date(2026, 10, 16))
    with pytest.raises(dataclasses.FrozenInstanceError):
        period.start = date(2026, 10, 6)  # type: ignore[misc]
