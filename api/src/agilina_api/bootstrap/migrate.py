"""Create and migrate every database of the platform (AD-29).

    make migrate

The catalog first (it is created if it does not exist), then the database of every tenant in
it, suspended ones included so that they never fall behind. Safe to repeat.
"""

import sys

from sqlalchemy import create_engine, text

from agilina_api.shared.infrastructure.migrations import ensure_database, migrate
from agilina_api.shared.infrastructure.settings import Settings, get_settings


def tenant_slugs(settings: Settings) -> list[str]:
    engine = create_engine(settings.platform_dsn)
    try:
        with engine.connect() as connection:
            return [
                row[0] for row in connection.execute(text("SELECT slug FROM tenant ORDER BY slug"))
            ]
    finally:
        engine.dispose()


def migrate_platform(settings: Settings) -> None:
    created = ensure_database(settings.admin_dsn, settings.platform_db)
    migrate("platform", settings.platform_dsn)
    print(f"Catalog {settings.platform_db}: {'created and ' if created else ''}migrated")


def migrate_tenant(settings: Settings, slug: str) -> None:
    database = f"{settings.tenant_db_prefix}{slug}"
    created = ensure_database(settings.admin_dsn, database)
    migrate("tenant", settings.tenant_dsn(slug))
    print(f"Tenant {slug} ({database}): {'created and ' if created else ''}migrated")


def main() -> int:
    settings = get_settings()
    migrate_platform(settings)
    for slug in tenant_slugs(settings):
        migrate_tenant(settings, slug)
    return 0


if __name__ == "__main__":
    sys.exit(main())
