"""Day N of M is a value: it cannot change after it is computed."""

from dataclasses import FrozenInstanceError

import pytest

from agilina_shared.sprint_calendar import SprintDay, SprintPhase


def test_a_sprint_day_cannot_be_changed():
    day = SprintDay(number=3, total=12, phase=SprintPhase.IN_PROGRESS)

    with pytest.raises(FrozenInstanceError):
        day.number = 4  # type: ignore[misc]


def test_two_sprint_days_with_the_same_values_are_equal():
    assert SprintDay(number=3, total=12, phase=SprintPhase.IN_PROGRESS) == SprintDay(
        number=3, total=12, phase=SprintPhase.IN_PROGRESS
    )
