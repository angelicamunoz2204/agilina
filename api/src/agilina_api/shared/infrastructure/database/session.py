"""Engines and async sessions.

Every database has its own engine (and so its own pool): the catalog and each tenant's. They
are created when first needed, so importing the application does not require a running
database: the smoke tests and the OpenAPI schema generation run without PostgreSQL.
"""

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)


def create_engine_for(dsn: str, *, echo: bool = False) -> AsyncEngine:
    """An engine for the database at ``dsn``. Nothing connects until it is used."""
    return create_async_engine(dsn, pool_pre_ping=True, echo=echo)


def create_session_factory(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(engine, expire_on_commit=False)
