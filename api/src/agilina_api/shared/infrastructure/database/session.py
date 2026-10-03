"""Engine and async session.

The engine is created lazily so that importing the application does not
require a running database: the smoke tests and the OpenAPI schema generation
run without Postgres.
"""

from collections.abc import AsyncIterator
from functools import lru_cache

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from agilina_api.shared.infrastructure.settings import get_settings


@lru_cache
def get_engine() -> AsyncEngine:
    settings = get_settings()
    return create_async_engine(
        settings.dsn,
        pool_pre_ping=True,
        echo=settings.log_level.upper() == "DEBUG",
    )


@lru_cache
def get_session_factory() -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(get_engine(), expire_on_commit=False)


async def get_session() -> AsyncIterator[AsyncSession]:
    """One session per request, always closed."""
    async with get_session_factory()() as session:
        yield session
