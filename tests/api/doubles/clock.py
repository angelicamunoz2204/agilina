"""The clock double: time moves only when the test says so."""

from datetime import datetime, timedelta

from tests.api.builders.defaults import NOW


class FakeClock:
    def __init__(self, now: datetime = NOW) -> None:
        self.current = now

    def now(self) -> datetime:
        return self.current

    def advance(self, **delta: float) -> None:
        self.current += timedelta(**delta)
