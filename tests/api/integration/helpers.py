"""Helpers shared by the integration tests: creating, migrating and dropping the database."""

from pathlib import Path

from alembic.config import Config
from sqlalchemy import create_engine, text

API_DIR = Path(__file__).resolve().parents[3] / "api"


def alembic_config() -> Config:
    config = Config(str(API_DIR / "alembic.ini"))
    config.set_main_option("script_location", str(API_DIR / "migrations"))
    return config


def create_database(admin_dsn: str, name: str) -> None:
    engine = create_engine(admin_dsn, isolation_level="AUTOCOMMIT")
    with engine.connect() as connection:
        connection.execute(text(f'CREATE DATABASE "{name}"'))
    engine.dispose()


def drop_database(admin_dsn: str, name: str) -> None:
    engine = create_engine(admin_dsn, isolation_level="AUTOCOMMIT")
    with engine.connect() as connection:
        connection.execute(text(f'DROP DATABASE IF EXISTS "{name}" WITH (FORCE)'))
    engine.dispose()
