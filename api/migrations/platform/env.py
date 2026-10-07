"""Alembic environment of the platform's catalog (AD-29).

Same as the tenants' (``migrations/tenant/env.py``): the URL is given by whoever runs the
migration. The catalog is not described by ORM models that tools could read, so there is no
metadata: its migrations are written by hand, in SQL, like every migration of the project.
"""

from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name, disable_existing_loggers=False)

url = config.attributes.get("url") or context.get_x_argument(as_dictionary=True).get("url")
if not url:
    raise RuntimeError("No database URL: pass it with `-x url=postgresql+psycopg://...`")
config.set_main_option("sqlalchemy.url", url)


def run_migrations_offline() -> None:
    """Generate the SQL without connecting: useful to review a migration before applying it."""
    context.configure(url=url, literal_binds=True, dialect_opts={"paramstyle": "named"})
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(connection=connection)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
