"""Common configuration of the API tests.

The smoke tests do not need Postgres: the application is built without
touching the database and the scheduler is disabled, so the pipeline does not
depend on infrastructure to go green.
"""

import logging

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from agilina_api.bootstrap.app import create_app
from agilina_api.shared.infrastructure.settings import get_settings
from agilina_api.shared.presentation.http.tenancy import get_tenant_directory
from tests.api.builders import TenantBuilder, reset_ids
from tests.api.doubles import FakeTenantDirectory


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
def tenants() -> FakeTenantDirectory:
    """The catalog the application is given: acme and ecomoda active, and initech suspended."""
    return FakeTenantDirectory(
        TenantBuilder().build(),
        TenantBuilder().ecomoda().build(),
        TenantBuilder().with_slug("initech").named("Initech").suspended().build(),
    )


@pytest.fixture
def app(tenants: FakeTenantDirectory) -> FastAPI:
    """The application with its real wiring, given the catalog of ``tenants``."""
    application = create_app()
    application.dependency_overrides[get_tenant_directory] = lambda: tenants
    return application


@pytest.fixture
async def client(app: FastAPI) -> AsyncClient:
    """HTTP client against the real wiring of the application, without starting a server or
    the lifespan and without a tenant header: each test names the tenant it is about."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://tests") as client:
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
