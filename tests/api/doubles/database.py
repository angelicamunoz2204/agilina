"""Doubles of the database session, for the failures a real PostgreSQL rarely produces."""

from types import SimpleNamespace
from typing import Any

from sqlalchemy.exc import IntegrityError


def integrity_error(constraint: str | None) -> IntegrityError:
    """What the driver raises when ``constraint`` (or an unnamed one) is violated."""
    diagnostics = SimpleNamespace(constraint_name=constraint)
    return IntegrityError("INSERT", {}, SimpleNamespace(diag=diagnostics))  # type: ignore[arg-type]


class FailingSession:
    """A session whose ``flush`` fails with ``error``: the database refused the row."""

    def __init__(self, error: Exception) -> None:
        self._error = error
        self.added: list[Any] = []

    def add(self, row: Any) -> None:
        self.added.append(row)

    async def flush(self) -> None:
        raise self._error


class RecordingSession:
    """A session that only remembers how it was closed or rolled back."""

    def __init__(self) -> None:
        self.closed = False
        self.rolled_back = False

    async def rollback(self) -> None:
        self.rolled_back = True

    async def close(self) -> None:
        self.closed = True

    async def __aenter__(self) -> "RecordingSession":
        return self

    async def __aexit__(self, *exc_info: object) -> None:
        await self.close()
