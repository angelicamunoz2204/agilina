"""``make invite``: how the command line becomes a call to ``invite`` (the flow itself is
tested against the database in ``tests/api/integration/bootstrap``)."""

import sys
from types import SimpleNamespace
from uuid import UUID

import pytest

from agilina_api.bootstrap import invite as invite_module
from agilina_api.shared.application.ports import MailDeliveryError
from agilina_api.shared.infrastructure.settings import get_settings
from agilina_api.shared_kernel import DomainError
from agilina_shared.enums import Language, TeamRole
from tests.api.builders import TenantBuilder, next_id


class _Container:
    closed = False
    built_for: list[str]

    async def aclose(self) -> None:
        self.closed = True


@pytest.fixture
def container(monkeypatch) -> _Container:
    """Every tenant asked for exists (acme, in English) and has this container."""
    built = _Container()
    built.built_for = []

    async def find(settings, slug):
        return TenantBuilder().with_slug(slug).build()

    def build(settings, tenant):
        built.built_for.append(tenant.slug)
        return built

    monkeypatch.setattr(invite_module, "find_tenant", find)
    monkeypatch.setattr(invite_module, "build_container", build)
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
        monkeypatch,
        "--tenant",
        "acme",
        "--email",
        "a@example.test",
        "--name",
        "Ana",
        "--team",
        "Atlas",
        "--lang",
        "en",
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
    assert container.built_for == ["acme"]


def test_without_a_language_the_team_and_the_email_speak_the_language_of_the_tenant(
    container, calls, monkeypatch
):
    _command_line(
        monkeypatch,
        "--tenant",
        "ecomoda",
        "--email",
        "a@example.test",
        "--name",
        "Ana",
        "--team",
        "Atlas",
    )

    assert invite_module.main() == 0
    assert calls[0]["language"] is Language.EN  # the double gives every tenant English
    assert container.built_for == ["ecomoda"]


def test_a_tenant_is_required(container, calls, monkeypatch):
    _command_line(monkeypatch, "--email", "a@example.test", "--name", "Ana", "--team", "Atlas")

    with pytest.raises(SystemExit):
        invite_module.main()


def test_an_existing_team_is_asked_for_by_id_and_the_role_can_change(container, calls, monkeypatch):
    team_id = next_id()
    _command_line(
        monkeypatch,
        "--tenant", "acme", "--email", "a@example.test", "--name", "Ana",
        "--team-id", str(team_id), "--role", "member",
    )  # fmt: skip

    assert invite_module.main() == 0
    assert calls[0]["team_id"] == UUID(str(team_id)) and calls[0]["role"] is TeamRole.MEMBER


def test_a_team_is_required(container, calls, monkeypatch):
    _command_line(monkeypatch, "--tenant", "acme", "--email", "a@example.test", "--name", "Ana")

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
    _command_line(
        monkeypatch,
        "--tenant",
        "acme",
        "--email",
        "a@example.test",
        "--name",
        "Ana",
        "--team",
        "Atlas",
    )

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


async def test_a_tenant_that_is_not_active_is_refused_by_name(monkeypatch):
    class Directory:
        async def find_active(self, slug):
            return None

    monkeypatch.setattr(invite_module, "SqlTenantDirectory", lambda factory, clock: Directory())
    monkeypatch.setattr(invite_module, "create_engine_for", lambda dsn: _Engine())

    with pytest.raises(DomainError, match="no active tenant 'initech'"):
        await invite_module.find_tenant(get_settings(), "initech")


async def test_an_active_tenant_is_found_in_the_catalog(monkeypatch):
    engine = _Engine()

    class Directory:
        async def find_active(self, slug):
            return TenantBuilder().with_slug(slug).build()

    monkeypatch.setattr(invite_module, "SqlTenantDirectory", lambda factory, clock: Directory())
    monkeypatch.setattr(invite_module, "create_engine_for", lambda dsn: engine)

    tenant = await invite_module.find_tenant(get_settings(), "ecomoda")

    assert tenant.slug == "ecomoda" and engine.disposed is True


class _Engine:
    disposed = False

    async def dispose(self) -> None:
        self.disposed = True
