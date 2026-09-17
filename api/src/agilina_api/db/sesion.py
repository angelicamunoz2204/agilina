"""Motor y sesión asíncrona.

El motor se crea de forma perezosa para que importar la aplicación no exija
una base de datos levantada: las pruebas de humo y la generación del esquema
de OpenAPI corren sin Postgres.
"""

from collections.abc import AsyncIterator
from functools import lru_cache

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from agilina_api.config import obtener_configuracion


@lru_cache
def obtener_motor() -> AsyncEngine:
    configuracion = obtener_configuracion()
    return create_async_engine(
        configuracion.dsn,
        pool_pre_ping=True,
        echo=configuracion.nivel_log.upper() == "DEBUG",
    )


@lru_cache
def obtener_fabrica_sesiones() -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(obtener_motor(), expire_on_commit=False)


async def obtener_sesion() -> AsyncIterator[AsyncSession]:
    """Dependencia de FastAPI: una sesión por petición, cerrada siempre."""
    async with obtener_fabrica_sesiones()() as sesion:
        yield sesion
