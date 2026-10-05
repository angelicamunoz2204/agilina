"""The probes: alive means the process runs; ready means its database answers."""

import pytest
from httpx import AsyncClient

from agilina_api.shared.infrastructure import database_probe


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
def database(monkeypatch):
    """Switch the database on or off: ``database(up=False)``."""

    def choose(*, up: bool) -> None:
        monkeypatch.setattr(
            database_probe, "get_session_factory", lambda: lambda: _Session(fails=not up)
        )

    return choose


async def test_the_liveness_probe_responds(client: AsyncClient):
    response = await client.get("/health")

    assert response.status_code == 200
    body = response.json()
    assert body["service"] == "agilina-api"
    assert body["status"] == "alive"
    assert body["version"]


async def test_the_readiness_probe_is_ready_when_the_database_answers(
    client: AsyncClient, database
):
    database(up=True)

    response = await client.get("/health/ready")

    assert response.status_code == 200
    assert response.json()["status"] == "ready" and response.json()["database"] == "available"


async def test_the_readiness_probe_answers_503_when_the_database_does_not(
    client: AsyncClient, database
):
    database(up=False)

    response = await client.get("/health/ready")

    assert response.status_code == 503
    assert response.json()["status"] != "ready" and response.json()["database"] == "unavailable"
