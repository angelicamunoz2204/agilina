"""Cross-cutting ports used by the use cases of every context."""

from datetime import datetime
from types import TracebackType
from typing import Protocol, Self


class Clock(Protocol):
    """The current instant, always in UTC (AD-20).

    A port so that time-dependent rules (a link that expires after seven days)
    are tested without waiting.
    """

    def now(self) -> datetime: ...


class UnitOfWork(Protocol):
    """A transaction around one use case.

    Entering it opens the transaction; ``commit`` makes the changes permanent
    and leaving without committing rolls them back.
    """

    async def __aenter__(self) -> Self: ...

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> None: ...

    async def commit(self) -> None: ...

    async def rollback(self) -> None: ...
