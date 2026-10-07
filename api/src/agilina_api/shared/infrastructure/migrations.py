"""Creating and migrating the databases of the platform (AD-29).

There are two kinds, each with its own Alembic environment: the catalog (``platform``) and
the database of every tenant (``tenant``). The URL is passed in by the caller: there is one
database per tenant, so no single URL can be configured.
"""

from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url

API_DIR = Path(__file__).resolve().parents[4]


def alembic_config(environment: str, url: str) -> Config:
    """The Alembic configuration of ``environment`` (``platform`` or ``tenant``) for ``url``."""
    config = Config(str(API_DIR / "alembic.ini"), ini_section=environment)
    config.set_main_option("script_location", str(API_DIR / "migrations" / environment))
    config.attributes["url"] = url
    return config


def database_name(dsn: str) -> str:
    name = make_url(dsn).database
    if name is None:
        raise ValueError("The URL names no database")
    return name


def ensure_database(admin_dsn: str, name: str) -> bool:
    """Creates the database ``name`` unless it exists. ``True`` when it was created."""
    engine = create_engine(admin_dsn, isolation_level="AUTOCOMMIT")
    try:
        with engine.connect() as connection:
            exists = connection.execute(
                text("SELECT 1 FROM pg_database WHERE datname = :name"), {"name": name}
            ).scalar()
            if exists:
                return False
            connection.execute(text(f'CREATE DATABASE "{name}"'))
            return True
    finally:
        engine.dispose()


def drop_database(admin_dsn: str, name: str) -> None:
    engine = create_engine(admin_dsn, isolation_level="AUTOCOMMIT")
    try:
        with engine.connect() as connection:
            connection.execute(text(f'DROP DATABASE IF EXISTS "{name}" WITH (FORCE)'))
    finally:
        engine.dispose()


def migrate(environment: str, url: str) -> None:
    """Applies every pending migration of ``environment`` to the database at ``url``."""
    command.upgrade(alembic_config(environment, url), "head")
