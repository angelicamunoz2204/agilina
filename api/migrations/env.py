"""Alembic environment.

The connection URL comes from the API settings, which read it from
environment variables: the repository stores no credentials, not even in the
Alembic file.
"""

from importlib import import_module
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

from agilina_api.shared.infrastructure.database.base import Base
from agilina_api.shared.infrastructure.settings import get_settings

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name, disable_existing_loggers=False)

config.set_main_option("sqlalchemy.url", get_settings().dsn)

# `import_module` registers each context's ORM models in `Base.metadata`, for the tools
# that read it. Do NOT use `alembic revision --autogenerate`: the ORM models are a
# deliberate subset of the tables (no foreign keys between contexts, no partial indexes,
# no triggers), so it proposes dropping real columns and constraints. Migrations are
# written by hand, in SQL (see docs/code-conventions.md).
for module in (
    "agilina_api.identity.infrastructure.persistence.orm_models",
    "agilina_api.teams.infrastructure.persistence.orm_models",
):
    import_module(module)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Generate the SQL without connecting: useful to review a migration before applying it."""
    context.configure(
        url=config.get_main_option("sqlalchemy.url"),
        target_metadata=target_metadata,
        literal_binds=True,
        compare_type=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata, compare_type=True)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
