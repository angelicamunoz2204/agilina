from datetime import datetime
from typing import Protocol


class Clock(Protocol):
    """The current instant, always in UTC (AD-20).

    A port so that time-dependent rules (a link that expires after seven days)
    are tested without waiting.
    """

    def now(self) -> datetime: ...
