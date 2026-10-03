"""Database health probe."""

from sqlalchemy import text

from agilina_api.shared.application.health import DatabaseProbe
from agilina_api.shared.infrastructure.database.session import get_session_factory
from agilina_api.shared.infrastructure.logging_setup import get_logger

logger = get_logger(__name__)


class SqlDatabaseProbe(DatabaseProbe):
    async def is_available(self) -> bool:
        try:
            async with get_session_factory()() as session:
                await session.execute(text("SELECT 1"))
        except Exception as error:  # any failure here means the database is unavailable
            logger.warning("The database is not responding: %s", error)
            return False
        return True
