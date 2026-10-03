"""System clock."""

from datetime import UTC, datetime

from agilina_api.shared.application.ports import Clock


class SystemClock(Clock):
    def now(self) -> datetime:
        return datetime.now(UTC)
