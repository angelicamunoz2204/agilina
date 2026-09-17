"""Configuración común de las pruebas de la API.

Las pruebas de humo no necesitan Postgres: la aplicación se construye sin
tocar la base de datos y el planificador se desactiva, de modo que el pipeline
no depende de infraestructura para dar verde.
"""

import pytest
from httpx import ASGITransport, AsyncClient

from agilina_api.config import obtener_configuracion
from agilina_api.main import crear_aplicacion


@pytest.fixture(autouse=True)
def entorno_de_pruebas(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("AGILINA_ENTORNO", "local")
    monkeypatch.setenv("AGILINA_NIVEL_LOG", "WARNING")
    obtener_configuracion.cache_clear()
    yield
    obtener_configuracion.cache_clear()


@pytest.fixture
async def cliente() -> AsyncClient:
    """Cliente HTTP contra la aplicación, sin levantar un servidor ni el ciclo de vida."""
    app = crear_aplicacion()
    transporte = ASGITransport(app=app)
    async with AsyncClient(transport=transporte, base_url="http://pruebas") as cliente:
        yield cliente
