"""The readiness probe says whether the database answers, without ever raising."""

from agilina_api.shared.infrastructure import database_probe
from agilina_api.shared.infrastructure.database_probe import SqlDatabaseProbe


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


async def test_a_database_that_answers_is_available(monkeypatch):
    monkeypatch.setattr(database_probe, "get_session_factory", lambda: lambda: _Session(False))

    assert await SqlDatabaseProbe().is_available() is True


async def test_a_database_that_does_not_answer_is_unavailable_and_it_is_logged(monkeypatch, caplog):
    monkeypatch.setattr(database_probe, "get_session_factory", lambda: lambda: _Session(True))

    assert await SqlDatabaseProbe().is_available() is False
    assert "connection refused" in caplog.text
