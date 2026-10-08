from dataclasses import dataclass
from datetime import UTC, datetime, time
from functools import cache
from zoneinfo import ZoneInfo, available_timezones

from agilina_api.teams.domain.errors import InvalidTimeZoneError


@cache
def _known_time_zones() -> frozenset[str]:
    """The IANA keys of the system's time zone database, read once.

    Checking the key against this set, instead of trying ``ZoneInfo(key)``, does not depend
    on which exception ``ZoneInfo`` raises for a path, a directory (``America``) or a key that
    only matches on a case-insensitive file system (``utc``).
    """
    return frozenset(available_timezones())


@dataclass(frozen=True)
class DailyTime:
    """The daily's time, one for the whole team: a UTC anchor instant plus the IANA time zone
    of the browser it was captured in (AD-31).

    The anchor is the chosen wall-clock time on one date, as an instant; it is kept in UTC and
    never as a local time. The wall-clock time the daily repeats every day of the sprint is
    the anchor seen in the capture time zone, so a daylight saving change does not move it.
    An anchor without an offset is not an instant and is rejected with ``ValueError``; a time
    zone that is not a known IANA key, with ``InvalidTimeZoneError``.
    """

    at: datetime
    time_zone: str

    def __post_init__(self) -> None:
        if self.at.tzinfo is None or self.at.utcoffset() is None:
            raise ValueError("The daily's time must be an aware datetime")
        if self.time_zone not in _known_time_zones():
            # The rejected value is not repeated: it comes from the request as it was sent.
            raise InvalidTimeZoneError("The daily's time zone is not a known IANA time zone")
        object.__setattr__(self, "at", self.at.astimezone(UTC))

    @property
    def zone(self) -> ZoneInfo:
        """The capture time zone: it fixes the wall-clock time and the sprint's calendar."""
        return ZoneInfo(self.time_zone)

    @property
    def local_time(self) -> time:
        """The daily's wall-clock time in the capture time zone (with no ``tzinfo``)."""
        return self.at.astimezone(self.zone).time()
