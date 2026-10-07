from datetime import date, datetime
from zoneinfo import ZoneInfo

from agilina_shared.sprint_calendar.sprint_day import SprintDay
from agilina_shared.sprint_calendar.sprint_phase import SprintPhase


def sprint_day_at(*, start: date, end: date, time_zone: ZoneInfo, now: datetime) -> SprintDay:
    """Day N of M of the sprint at the instant ``now``, without reading the clock.

    ``now`` is the current instant, which the caller takes from its ``Clock`` in UTC (AD-20);
    a naive value is rejected with ``ValueError``. Today is the date of ``now`` in
    ``time_zone``, the daily's capture time zone, so the day changes at local midnight and not
    at UTC midnight. M counts every calendar day from ``start`` to ``end``, both included and
    weekends too. Before ``start`` the sprint is ``not_started`` (N=0), from ``start`` to
    ``end`` it is ``in_progress`` (N from 1 to M) and after ``end`` it is ``finished`` (N=M).

    ``end`` before ``start`` is not a sprint and is rejected with ``ValueError``.
    """
    if now.tzinfo is None or now.utcoffset() is None:
        raise ValueError("now must be an aware datetime")
    if end < start:
        raise ValueError("end must not be before start")
    total = (end - start).days + 1
    today = now.astimezone(time_zone).date()
    if today < start:
        return SprintDay(number=0, total=total, phase=SprintPhase.NOT_STARTED)
    if today > end:
        return SprintDay(number=total, total=total, phase=SprintPhase.FINISHED)
    return SprintDay(number=(today - start).days + 1, total=total, phase=SprintPhase.IN_PROGRESS)
