from dataclasses import dataclass

from agilina_shared.sprint_calendar.sprint_phase import SprintPhase


@dataclass(frozen=True, kw_only=True)
class SprintDay:
    """Day N of M of a sprint at a given instant.

    ``total`` (M) is the number of calendar days of the period, both ends included. ``number``
    (N) is 0 before the first day, 1..M while the sprint is in progress and M once it is over.
    """

    number: int
    total: int
    phase: SprintPhase
