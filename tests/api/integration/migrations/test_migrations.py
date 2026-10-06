"""The migrations produce the schema the reference DDL defines (with AD-22 and the minimal
sprint of HU-06), and the ORM models agree with it."""

import uuid
from datetime import date

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

    assert {"app_user", "team", "team_member", "invitation", "sprint", "alembic_version"} <= tables


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
        "sprint_status",
    } <= enums


@pytest.mark.parametrize("table", ["team", "invitation"])
async def test_created_by_accepts_null_for_the_platform_operator_ad_22(
    engine: AsyncEngine, table: str
):
    assert (await _columns(engine, table))["created_by"] is True


@pytest.mark.parametrize("table", ["app_user", "team", "team_member", "invitation", "sprint"])
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


async def test_the_sprint_statuses_are_the_glossarys(engine: AsyncEngine):
    async with engine.connect() as connection:
        labels = (
            await connection.execute(text("SELECT unnest(enum_range(NULL::sprint_status))::text"))
        ).scalars()

    assert list(labels) == ["planned", "active", "closed"]


async def _a_team(engine: AsyncEngine) -> str:
    async with engine.begin() as connection:
        return str(
            (
                await connection.execute(
                    text("INSERT INTO team (name) VALUES ('Atlas') RETURNING id")
                )
            ).scalar_one()
        )


_SPRINT = text(
    "INSERT INTO sprint (team_id, start_date, end_date, status) "
    "VALUES (:team, :start, :end, CAST(:status AS sprint_status))"
)


async def test_a_new_sprint_is_planned_and_cannot_end_before_it_starts(engine: AsyncEngine):
    team = await _a_team(engine)
    async with engine.begin() as connection:
        await connection.execute(
            text("INSERT INTO sprint (team_id, start_date, end_date) VALUES (:t, :d, :d)"),
            {"t": team, "d": date(2026, 10, 5)},
        )
        status = (await connection.execute(text("SELECT status::text FROM sprint"))).scalar_one()
    assert status == "planned"

    with pytest.raises(IntegrityError, match="sprint_dates_ordered"):
        async with engine.begin() as connection:
            await connection.execute(
                _SPRINT,
                {
                    "team": team,
                    "start": date(2026, 10, 5),
                    "end": date(2026, 10, 4),
                    "status": "planned",
                },
            )


async def test_a_team_has_at_most_one_active_sprint_but_any_number_of_closed_ones(
    engine: AsyncEngine,
):
    team = await _a_team(engine)
    dates = {"start": date(2026, 10, 5), "end": date(2026, 10, 16)}
    async with engine.begin() as connection:
        for status in ("closed", "closed", "active"):
            await connection.execute(_SPRINT, {"team": team, "status": status, **dates})

    with pytest.raises(IntegrityError, match="sprint_one_active_per_team"):
        async with engine.begin() as connection:
            await connection.execute(_SPRINT, {"team": team, "status": "active", **dates})


async def test_deleting_a_team_deletes_its_sprints(engine: AsyncEngine):
    team = await _a_team(engine)
    async with engine.begin() as connection:
        await connection.execute(
            _SPRINT,
            {
                "team": team,
                "start": date(2026, 10, 5),
                "end": date(2026, 10, 16),
                "status": "active",
            },
        )
        await connection.execute(text("DELETE FROM team WHERE id = :id"), {"id": team})
        remaining = (await connection.execute(text("SELECT count(*) FROM sprint"))).scalar_one()

    assert remaining == 0


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
            command.downgrade(alembic_config(), "0003_team_name_max_length")

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
            assert "sprint" not in tables and "sprint_status" not in enums  # HU-06 undone
            assert "team" in tables

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
            assert not {"app_user", "team", "team_member", "invitation", "sprint"} & tables
            assert not {"team_role", "invitation_status", "sprint_status"} & enums

            command.upgrade(alembic_config(), "head")
    finally:
        get_settings.cache_clear()
        drop_database(admin_dsn, name)
