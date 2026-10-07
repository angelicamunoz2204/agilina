"""``make migrate``: the catalog and the database of every tenant, created and migrated."""

import pytest
from sqlalchemy import create_engine, inspect, text

from agilina_api.bootstrap import migrate as migrate_module
from agilina_api.shared.infrastructure.migrations import drop_database, ensure_database
from tests.api.integration.conftest import PlatformDatabases

pytestmark = pytest.mark.integration


def _tables(dsn: str) -> set[str]:
    engine = create_engine(dsn)
    try:
        with engine.connect() as connection:
            return set(inspect(connection).get_table_names())
    finally:
        engine.dispose()


def test_the_catalog_lists_its_tenants_by_slug(platform_databases: PlatformDatabases):
    assert migrate_module.tenant_slugs(platform_databases.settings) == ["acme", "ecomoda"]


def test_a_tenant_database_that_does_not_exist_is_created_and_migrated(
    platform_databases: PlatformDatabases, capsys
):
    settings = platform_databases.settings

    migrate_module.migrate_tenant(settings, "wonka")
    try:
        assert {"app_user", "team", "team_member", "invitation"} <= _tables(
            settings.tenant_dsn("wonka")
        )
        assert "created and migrated" in capsys.readouterr().out
    finally:
        drop_database(settings.admin_dsn, f"{platform_databases.prefix}wonka")


def test_migrating_again_changes_nothing_and_says_so(platform_databases: PlatformDatabases, capsys):
    settings = platform_databases.settings

    migrate_module.migrate_tenant(settings, "acme")

    out = capsys.readouterr().out
    assert "created" not in out and "migrated" in out


def test_the_whole_platform_is_migrated_walking_the_catalog(
    platform_databases: PlatformDatabases, capsys
):
    """A tenant that is in the catalog but whose database is missing gets it."""
    settings = platform_databases.settings
    catalog = create_engine(settings.platform_dsn)
    with catalog.begin() as connection:
        connection.execute(
            text(
                "INSERT INTO tenant (slug, display_name, status) "
                "VALUES ('wonka', 'Wonka', 'suspended')"
            )
        )
    try:
        assert migrate_module.main() == 0

        out = capsys.readouterr().out
        assert "Catalog" in out and "Tenant acme" in out and "Tenant wonka" in out
        # Suspended tenants are migrated too, so that they never fall behind.
        assert "app_user" in _tables(settings.tenant_dsn("wonka"))
    finally:
        with catalog.begin() as connection:
            connection.execute(text("DELETE FROM tenant WHERE slug = 'wonka'"))
        catalog.dispose()
        drop_database(settings.admin_dsn, f"{platform_databases.prefix}wonka")


def test_the_catalog_database_is_created_when_it_is_missing(platform_databases: PlatformDatabases):
    settings = platform_databases.settings.model_copy(
        update={"platform_db": f"{platform_databases.prefix}other_platform"}
    )
    try:
        migrate_module.migrate_platform(settings)

        assert "tenant" in _tables(settings.platform_dsn)
    finally:
        drop_database(settings.admin_dsn, settings.platform_db)


def test_ensure_database_creates_once(platform_databases: PlatformDatabases):
    settings = platform_databases.settings
    name = f"{platform_databases.prefix}scratch"
    try:
        assert ensure_database(settings.admin_dsn, name) is True
        assert ensure_database(settings.admin_dsn, name) is False
    finally:
        drop_database(settings.admin_dsn, name)
