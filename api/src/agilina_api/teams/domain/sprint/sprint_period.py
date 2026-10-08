from dataclasses import dataclass
from datetime import date

from agilina_api.teams.domain.errors import SprintEndsBeforeStartError


@dataclass(frozen=True)
class SprintPeriod:
    """The calendar dates of a sprint, both included and with no time of day.

    They may fall on any day of the week, and every day of the period counts, weekends
    included (AD-31), so the only rule is that the end does not come before the start: a
    sprint of a single day (start equal to end) is valid. Which calendar "today" belongs to is
    the daily's capture time zone, not this value's concern.
    """

    start: date
    end: date

    def __post_init__(self) -> None:
        if self.end < self.start:
            raise SprintEndsBeforeStartError("A sprint cannot end before it starts")
