"""The migrations produce the schema the reference DDL defines (with AD-22), and the ORM
models agree with it."""

import uuid

import pytest
from alembic import command
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine import make_url
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncEngine

from agilina_api.identity.infrastructure.persistence import orm_models as identity_models
from agilina_api.shared.infrastructure.database.base import Base
from agilina_api.shared.infrastructure.settings import get_settings
from agilina_api.teams.infrastructure.persistence import orm_models as teams_models
from tests.api.integration.helpers import alembic_config, create_database, drop_database

pytestmark = pytest.mark.integration

_REGISTERED = (identity_models, teams_models)  # the models must be imported to be in the metadata


async def _columns(engine: AsyncEngine, table: str) -> dict[str, bool]:
    """Column name → nullable, as the database reports it."""
    async with engine.connect() as connection:
        found = await connection.run_sync(lambda sync: inspect(sync).get_columns(table))
    return {column["name"]: column["nullable"] for column in found}


async def test_every_table_the_story_needs_exists(engine: AsyncEngine):
    async with engine.connect() as connection:
        tables = await connection.run_sync(lambda sync: set(inspect(sync).get_table_names()))

    assert {"app_user", "team", "team_member", "invitation", "alembic_version"} <= tables


async def test_citext_and_the_enums_exist(engine: AsyncEngine):
    async with engine.connect() as connection:
        extensions = {
            row[0] for row in await connection.execute(text("SELECT extname FROM pg_extension"))
        }
        enums = {
            row[0]
            for row in await connection.execute(
                text("SELECT typname FROM pg_type WHERE typtype = 'e'")
            )
        }

    assert "citext" in extensions
    assert {
        "team_mode",
        "team_language",
        "team_role",
        "membership_status",
        "invitation_status",
    } <= enums


@pytest.mark.parametrize("table", ["team", "invitation"])
async def test_created_by_accepts_null_for_the_platform_operator_ad_22(
    engine: AsyncEngine, table: str
):
    assert (await _columns(engine, table))["created_by"] is True


@pytest.mark.parametrize("table", ["app_user", "team", "team_member", "invitation"])
async def test_every_orm_column_exists_in_the_database_with_the_same_nullability(
    engine: AsyncEngine, table: str
):
    in_database = await _columns(engine, table)

    for column in Base.metadata.tables[table].columns:
        assert column.name in in_database, f"{table}.{column.name} is not in the database"
        assert column.nullable == in_database[column.name], f"{table}.{column.name} nullability"


async def test_the_partial_unique_index_on_pending_invitations_exists(engine: AsyncEngine):
    async with engine.connect() as connection:
        definition = (
            await connection.execute(
                text(
                    "SELECT indexdef FROM pg_indexes WHERE indexname = 'invitation_pending_unique'"
                )
            )
        ).scalar_one()

    assert "UNIQUE" in definition and "status = 'pending'" in definition


async def test_the_database_rejects_a_team_name_longer_than_80(engine: AsyncEngine):
    """The ``team_name_max_length`` check backs the domain rule: 80 is fine, 81 is not."""
    insert = text("INSERT INTO team (name) VALUES (:name)")
    async with engine.begin() as connection:
        await connection.execute(insert, {"name": "x" * 80})
        await connection.execute(insert, {"name": "🚀" * 80})  # characters, not bytes

    with pytest.raises(IntegrityError, match="team_name_max_length"):
        async with engine.begin() as connection:
            await connection.execute(insert, {"name": "x" * 81})


def test_the_migrations_go_down_and_up_again_cleanly(admin_dsn: str):
    """Downgrading removes everything the migration created, and upgrading restores it."""
    name = f"agilina_it_{uuid.uuid4().hex[:12]}"
    url = make_url(admin_dsn).set(database=name).render_as_string(hide_password=False)
    create_database(admin_dsn, name)
    try:
        with pytest.MonkeyPatch.context() as patch:
            patch.setenv("AGILINA_DB_URL", url)
            get_settings.cache_clear()
            command.upgrade(alembic_config(), "head")
            command.downgrade(alembic_config(), "0001_base")

            engine = create_engine(url)
            with engine.connect() as connection:
                tables = set(inspect(connection).get_table_names())
                enums = {
                    r[0]
                    for r in connection.execute(
                        text("SELECT typname FROM pg_type WHERE typtype='e'")
                    )
                }
            engine.dispose()
            assert not {"app_user", "team", "team_member", "invitation"} & tables
            assert not {"team_role", "invitation_status"} & enums

            command.upgrade(alembic_config(), "head")
    finally:
        get_settings.cache_clear()
        drop_database(admin_dsn, name)
