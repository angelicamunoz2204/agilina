"""Entorno de Alembic.

La URL de conexión llega de la configuración de la API, que la lee de
variables de entorno: el repositorio no guarda credenciales ni siquiera en el
archivo de Alembic.
"""

from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

from agilina_api.config import obtener_configuracion
from agilina_api.db.base import Base

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

config.set_main_option("sqlalchemy.url", obtener_configuracion().dsn)

# Las entidades del dominio se importan aquí a medida que las historias las
# incorporan, para que `alembic revision --autogenerate` las vea:
#   from agilina_api.modelos import equipos, ceremonias  # noqa: F401
target_metadata = Base.metadata


def ejecutar_migraciones_sin_conexion() -> None:
    """Genera el SQL sin conectarse: útil para revisar una migración antes de aplicarla."""
    context.configure(
        url=config.get_main_option("sqlalchemy.url"),
        target_metadata=target_metadata,
        literal_binds=True,
        compare_type=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def ejecutar_migraciones_con_conexion() -> None:
    conectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with conectable.connect() as conexion:
        context.configure(connection=conexion, target_metadata=target_metadata, compare_type=True)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    ejecutar_migraciones_sin_conexion()
else:
    ejecutar_migraciones_con_conexion()
