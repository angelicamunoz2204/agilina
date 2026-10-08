from datetime import UTC, date, datetime, time, timedelta
from zoneinfo import ZoneInfo


def daily_occurrences(
    *, start: date, end: date, local_time: time, time_zone: ZoneInfo
) -> tuple[datetime, ...]:
    """The UTC instants of the daily: the same wall-clock time on every day of the period.

    One occurrence per calendar date from ``start`` to ``end``, both included and weekends
    too, in chronological order; an empty tuple when ``end`` is before ``start``. Each one is
    ``local_time`` on that date in ``time_zone`` (the capture time zone), converted to UTC, so
    a daylight saving change keeps the wall-clock time and an early daily east of UTC is never
    moved to another date.

    A wall-clock time that does not exist on a date (the gap of a spring change) or that
    exists twice (the fold of an autumn change) is resolved with ``fold=0``, the offset in
    force before the change: 02:30 on 2027-03-14 in America/New_York gives 07:30Z, and 01:30
    on 2027-11-07 gives 05:30Z. Any ``fold`` or ``tzinfo`` carried by ``local_time`` is ignored.
    """
    wall_clock = local_time.replace(tzinfo=None, fold=0)
    dates = (start + timedelta(days=offset) for offset in range((end - start).days + 1))
    return tuple(
        datetime.combine(day, wall_clock, tzinfo=time_zone).astimezone(UTC) for day in dates
    )
