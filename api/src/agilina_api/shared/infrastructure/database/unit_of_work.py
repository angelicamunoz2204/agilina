"""SQLAlchemy implementation of the ``UnitOfWork`` port: one transaction per use case."""

from types import TracebackType
from typing import Self

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from agilina_api.shared.application.ports import UnitOfWork


class SqlAlchemyUnitOfWork(UnitOfWork):
    """Entering it opens a session (and with it the transaction); ``commit`` makes the
    changes permanent, and leaving without committing, or with an error, discards them."""

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory
        self._session: AsyncSession | None = None

    @property
    def session(self) -> AsyncSession:
        """The session repositories use. Only available inside ``async with``."""
        if self._session is None:
            raise RuntimeError("The unit of work is not open: use it with `async with`")
        return self._session

    async def __aenter__(self) -> Self:
        self._session = self._session_factory()
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        session, self._session = self._session, None
        if session is not None:
            await session.rollback()  # a no-op after commit; discards everything otherwise
            await session.close()

    async def commit(self) -> None:
        await self.session.commit()

    async def rollback(self) -> None:
        await self.session.rollback()
