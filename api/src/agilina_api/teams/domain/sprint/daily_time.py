from dataclasses import dataclass
from datetime import UTC, datetime, time
from zoneinfo import ZoneInfo


@dataclass(frozen=True)
class DailyTime:
    """The daily's time, one for the whole team: a UTC anchor instant plus the IANA time zone
    of the browser it was captured in (AD-31).

    The anchor is the chosen wall-clock time on one date, as an instant; it is kept in UTC and
    never as a local time. The wall-clock time the daily repeats every day of the sprint is
    the anchor seen in the capture time zone, so a daylight saving change does not move it.
    An anchor without an offset is not an instant and is rejected with ``ValueError``.
    """

    at: datetime
    time_zone: str

    def __post_init__(self) -> None:
        if self.at.tzinfo is None or self.at.utcoffset() is None:
            raise ValueError("The daily's time must be an aware datetime")
        object.__setattr__(self, "at", self.at.astimezone(UTC))

    @property
    def zone(self) -> ZoneInfo:
        """The capture time zone: it fixes the wall-clock time and the sprint's calendar."""
        return ZoneInfo(self.time_zone)

    @property
    def local_time(self) -> time:
        """The daily's wall-clock time in the capture time zone (with no ``tzinfo``)."""
        return self.at.astimezone(self.zone).time()
