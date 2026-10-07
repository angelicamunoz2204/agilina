"""The sprint phase travels as text (API responses, the web): its values are part of the
contract and must not change by accident."""

from agilina_shared.sprint_calendar import SprintPhase


def test_the_phases_travel_as_these_values():
    assert [phase.value for phase in SprintPhase] == ["not_started", "in_progress", "finished"]


def test_a_phase_is_read_back_from_its_value():
    assert SprintPhase("in_progress") is SprintPhase.IN_PROGRESS
