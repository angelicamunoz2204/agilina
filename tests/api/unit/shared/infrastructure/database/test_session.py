"""The request-scoped session: one per request, always closed."""

from agilina_api.shared.infrastructure.database import session as session_module
from tests.api.doubles.database import RecordingSession


async def test_a_session_is_handed_out_and_closed_afterwards(monkeypatch):
    recording = RecordingSession()
    monkeypatch.setattr(session_module, "get_session_factory", lambda: lambda: recording)

    generator = session_module.get_session()
    handed_out = await anext(generator)

    assert handed_out is recording and recording.closed is False
    await generator.aclose()
    assert recording.closed is True
