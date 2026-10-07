"""Database health probe."""

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from agilina_api.shared.application.health import DatabaseProbe
from agilina_api.shared.infrastructure.logging_setup import get_logger

logger = get_logger(__name__)


class SqlDatabaseProbe(DatabaseProbe):
    """Whether the platform's database, the catalog of tenants, answers."""

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def is_available(self) -> bool:
        try:
            async with self._session_factory() as session:
                await session.execute(text("SELECT 1"))
        except Exception as error:  # any failure here means the database is unavailable
            logger.warning("The database is not responding: %s", error)
            return False
        return True
