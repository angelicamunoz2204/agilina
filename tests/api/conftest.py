"""Common configuration of the API tests.

The smoke tests do not need Postgres: the application is built without
touching the database and the scheduler is disabled, so the pipeline does not
depend on infrastructure to go green.
"""

import logging

import pytest
from httpx import ASGITransport, AsyncClient

from agilina_api.bootstrap.app import create_app
from agilina_api.shared.infrastructure.settings import get_settings
from tests.api.builders import reset_ids


@pytest.fixture(autouse=True)
def fresh_identifiers() -> None:
    """Every test counts its identifiers from 1: a failure is reproducible."""
    reset_ids()


@pytest.fixture(autouse=True)
def test_environment(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("AGILINA_ENVIRONMENT", "local")
    monkeypatch.setenv("AGILINA_LOG_LEVEL", "WARNING")
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


@pytest.fixture
async def client() -> AsyncClient:
    """HTTP client against the application, without starting a server or the lifespan."""
    transport = ASGITransport(app=create_app())
    async with AsyncClient(transport=transport, base_url="http://tests") as client:
        yield client


@pytest.fixture
def untouched_logging():
    """``configure_logging`` replaces the root handlers: put them back afterwards."""
    root = logging.getLogger()
    handlers, level = list(root.handlers), root.level
    access = logging.getLogger("uvicorn.access")
    propagate = access.propagate
    yield
    root.handlers[:], root.level = handlers, level
    access.propagate = propagate
