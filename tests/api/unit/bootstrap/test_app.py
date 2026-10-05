"""The application factory and its lifespan (start and stop of the scheduler)."""

import pytest

from agilina_api.bootstrap import app as app_module
from agilina_api.bootstrap.app import create_app, lifespan


class _Scheduler:
    def __init__(self, *, fails_to_start: bool = False) -> None:
        self.fails_to_start = fails_to_start
        self.running = False
        self.shut_down = False

    def start(self) -> None:
        if self.fails_to_start:
            raise ConnectionError("the database is down")
        self.running = True

    def shutdown(self, *, wait: bool) -> None:
        self.shut_down = not wait


@pytest.fixture
def scheduler(monkeypatch) -> _Scheduler:
    chosen = _Scheduler()
    monkeypatch.setattr(app_module, "create_scheduler", lambda settings: chosen)
    return chosen


def test_every_context_exposes_its_routes():
    paths = create_app().openapi()["paths"]

    assert "/health" in paths
    assert "/v1/invitations/activate" in paths
    assert "/v1/ceremonies/{ceremony_id}/context" in paths
    assert "/v1/teams" in paths
    assert "/v1/teams/{team_id}" in paths


async def test_the_scheduler_starts_with_the_application_and_stops_with_it(
    scheduler, untouched_logging
):
    app = create_app()

    async with lifespan(app):
        assert app.state.scheduler is scheduler and scheduler.running is True

    assert scheduler.shut_down is True
    assert app.state.container.identity_provider._client.is_closed is True  # noqa: SLF001


async def test_without_a_database_the_api_still_starts_without_a_scheduler(
    scheduler, untouched_logging, capsys
):
    scheduler.fails_to_start = True
    app = create_app()

    async with lifespan(app):
        assert app.state.scheduler is None

    assert "could not start" in capsys.readouterr().out  # the lifespan configures logging itself
    assert scheduler.shut_down is False
