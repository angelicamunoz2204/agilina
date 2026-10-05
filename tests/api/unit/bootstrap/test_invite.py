"""``make invite``: how the command line becomes a call to ``invite`` (the flow itself is
tested against the database in ``tests/api/integration/bootstrap``)."""

import sys
from types import SimpleNamespace
from uuid import UUID

import pytest

from agilina_api.bootstrap import invite as invite_module
from agilina_api.shared.application.ports import MailDeliveryError
from agilina_api.shared_kernel import DomainError
from agilina_shared.enums import Language, TeamRole
from tests.api.builders import next_id


class _Container:
    closed = False

    async def aclose(self) -> None:
        self.closed = True


@pytest.fixture
def container(monkeypatch) -> _Container:
    built = _Container()
    monkeypatch.setattr(invite_module, "build_container", lambda settings: built)
    return built


@pytest.fixture
def calls(monkeypatch) -> list[dict]:
    recorded: list[dict] = []

    async def record(_container, **arguments):
        recorded.append(arguments)

    monkeypatch.setattr(invite_module, "invite", record)
    return recorded


def _command_line(monkeypatch, *arguments: str) -> None:
    monkeypatch.setattr(sys, "argv", ["invite", *arguments])


def test_a_new_team_is_asked_for_by_name(container, calls, monkeypatch):
    _command_line(
        monkeypatch, "--email", "a@example.test", "--name", "Ana", "--team", "Atlas", "--lang", "en"
    )

    assert invite_module.main() == 0
    assert calls == [
        {
            "email": "a@example.test",
            "full_name": "Ana",
            "role": TeamRole.ADMIN,
            "language": Language.EN,
            "team_name": "Atlas",
            "team_id": None,
        }
    ]
    assert container.closed is True


def test_an_existing_team_is_asked_for_by_id_and_the_role_can_change(container, calls, monkeypatch):
    team_id = next_id()
    _command_line(
        monkeypatch,
        "--email", "a@example.test", "--name", "Ana",
        "--team-id", str(team_id), "--role", "member",
    )  # fmt: skip

    assert invite_module.main() == 0
    assert calls[0]["team_id"] == UUID(str(team_id)) and calls[0]["role"] is TeamRole.MEMBER


def test_a_team_is_required(container, calls, monkeypatch):
    _command_line(monkeypatch, "--email", "a@example.test", "--name", "Ana")

    with pytest.raises(SystemExit):
        invite_module.main()


@pytest.mark.parametrize(
    ("error", "message"),
    [
        (MailDeliveryError("smtp down"), "email failed"),
        (DomainError("no such team"), "Not done: no such team"),
    ],
)
def test_a_known_failure_is_explained_and_exits_with_an_error(
    container, monkeypatch, capsys, error, message
):
    async def fail(_container, **arguments):
        raise error

    monkeypatch.setattr(invite_module, "invite", fail)
    _command_line(monkeypatch, "--email", "a@example.test", "--name", "Ana", "--team", "Atlas")

    assert invite_module.main() == 1
    assert message in capsys.readouterr().err
    assert container.closed is True


async def test_an_unknown_team_id_is_refused_by_name(monkeypatch):
    team_queries = SimpleNamespace(get_summary=_nothing)

    with pytest.raises(DomainError, match="There is no team"):
        await invite_module.invite(
            SimpleNamespace(team_queries=team_queries),  # type: ignore[arg-type]
            email="a@example.test",
            full_name="Ana",
            role=TeamRole.ADMIN,
            language=Language.EN,
            team_name=None,
            team_id=next_id(),
        )


async def _nothing(team_id):
    return None
