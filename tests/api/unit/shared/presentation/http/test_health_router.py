"""The probes: alive means the process runs; ready means the catalog's database answers."""

import pytest
from fastapi import FastAPI
from httpx import AsyncClient

from agilina_api import __version__
from agilina_api.shared.application.health import GetReadiness
from agilina_api.shared.infrastructure.database_probe import SqlDatabaseProbe
from agilina_api.shared.presentation.http.dependencies import get_readiness_query


class _Session:
    def __init__(self, fails: bool) -> None:
        self._fails = fails

    async def __aenter__(self) -> "_Session":
        return self

    async def __aexit__(self, *exc_info: object) -> None:
        return None

    async def execute(self, statement: object) -> None:
        if self._fails:
            raise ConnectionError("connection refused")


@pytest.fixture
def database(app: FastAPI):
    """Switch the catalog's database on or off: ``database(up=False)``."""

    def choose(*, up: bool) -> None:
        probe = SqlDatabaseProbe(lambda: _Session(fails=not up))
        app.dependency_overrides[get_readiness_query] = lambda: GetReadiness(
            probe, __version__, "local"
        )

    return choose


async def test_the_liveness_probe_responds_without_a_tenant(client: AsyncClient):
    response = await client.get("/health")

    assert response.status_code == 200
    body = response.json()
    assert body["service"] == "agilina-api"
    assert body["status"] == "alive"
    assert body["version"]


async def test_the_readiness_probe_is_ready_when_the_database_answers(client, database):
    database(up=True)

    response = await client.get("/health/ready")

    assert response.status_code == 200
    assert response.json()["status"] == "ready" and response.json()["database"] == "available"


async def test_the_readiness_probe_answers_503_when_the_database_does_not(client, database):
    database(up=False)

    response = await client.get("/health/ready")

    assert response.status_code == 503
    assert response.json()["status"] != "ready" and response.json()["database"] == "unavailable"
