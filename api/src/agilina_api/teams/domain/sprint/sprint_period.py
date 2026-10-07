from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class SprintPeriod:
    """The calendar dates of a sprint, both included and with no time of day.

    They may fall on any day of the week, and every day of the period counts, weekends
    included (AD-31). Which calendar "today" belongs to is the daily's capture time zone, not
    this value's concern.
    """

    start: date
    end: date
