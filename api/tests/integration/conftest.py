"""Integration tests run against a real PostgreSQL (``make test-integration``).

Each run creates a throwaway database, applies every migration to it and drops it at the
end, so the schema under test is the one the migrations really produce and the
developer's own data is never touched.
"""

import uuid
from collections.abc import AsyncIterator, Iterator

import pytest
from alembic import command
from integration_helpers import alembic_config, create_database, drop_database
from sqlalchemy import text
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import NullPool

from agilina_api.shared.infrastructure.database.unit_of_work import SqlAlchemyUnitOfWork
from agilina_api.shared.infrastructure.settings import get_settings

TABLES = "invitation, team_member, team, app_user"


@pytest.fixture(scope="session")
def admin_dsn() -> str:
    get_settings.cache_clear()
    return get_settings().dsn


@pytest.fixture(scope="session")
def database_url(admin_dsn: str) -> Iterator[str]:
    """A fresh database with every migration applied."""
    name = f"agilina_it_{uuid.uuid4().hex[:12]}"
    url = make_url(admin_dsn).set(database=name).render_as_string(hide_password=False)
    create_database(admin_dsn, name)
    with pytest.MonkeyPatch.context() as patch:
        patch.setenv("AGILINA_DB_URL", url)  # alembic's env.py reads the URL from the settings
        get_settings.cache_clear()
        command.upgrade(alembic_config(), "head")
        yield url
    get_settings.cache_clear()
    drop_database(admin_dsn, name)


@pytest.fixture
async def engine(database_url: str) -> AsyncIterator[AsyncEngine]:
    engine = create_async_engine(database_url, poolclass=NullPool)
    async with engine.begin() as connection:
        await connection.execute(text(f"TRUNCATE {TABLES} CASCADE"))
    yield engine
    await engine.dispose()


@pytest.fixture
def session_factory(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(engine, expire_on_commit=False)


@pytest.fixture
def uow(session_factory: async_sessionmaker[AsyncSession]) -> SqlAlchemyUnitOfWork:
    """A new unit of work; use it with ``async with``."""
    return SqlAlchemyUnitOfWork(session_factory)
