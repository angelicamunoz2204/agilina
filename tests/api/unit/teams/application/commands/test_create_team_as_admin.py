"""CreateTeamAsAdmin: a user creates a team and becomes its admin, in one transaction."""

from uuid import UUID

import pytest

from agilina_api.teams.application.commands.create_team_as_admin import (
    CreateTeamAsAdmin,
    CreateTeamAsAdminHandler,
)
from agilina_api.teams.domain.errors import InvalidTeamNameError
from agilina_api.teams.domain.team import Team
from agilina_shared.enums import Language, OperationMode, TeamRole
from tests.api.builders import NOW, next_id
from tests.api.doubles import FakeClock, FakeTeamsUnitOfWork


def _handler(uow: FakeTeamsUnitOfWork) -> CreateTeamAsAdminHandler:
    return CreateTeamAsAdminHandler(lambda: uow, FakeClock(), new_id=next_id)


async def _create(name: str = "  Atlas  ") -> tuple[FakeTeamsUnitOfWork, UUID, Team]:
    """Ana creates a team: returns the unit of work, Ana and the stored team."""
    uow, ana = FakeTeamsUnitOfWork(), next_id()
    team_id = await _handler(uow).handle(CreateTeamAsAdmin(name=name, user_id=ana))
    return uow, ana, uow.teams.teams[team_id]


async def test_the_team_is_created_with_support_mode_and_english():
    _, _, team = await _create()

    assert team.mode is OperationMode.SUPPORT
    assert team.language is Language.EN
    assert team.name == "Atlas" and team.created_at == NOW


async def test_the_creator_becomes_an_active_admin():
    _, ana, team = await _create()

    membership = team.membership_of(ana)
    assert membership is not None
    assert membership.role is TeamRole.ADMIN and membership.is_active
    assert len(team.memberships) == 1


async def test_the_creator_is_recorded_as_created_by():
    _, ana, team = await _create()

    assert team.created_by == ana


async def test_the_team_and_its_admin_are_committed_together():
    uow, _, team = await _create()

    assert uow.committed is True
    assert list(uow.teams.teams.values()) == [team]


@pytest.mark.parametrize("name", ["", "   ", "x" * 81])
async def test_a_blank_name_creates_nothing(name):
    uow = FakeTeamsUnitOfWork()

    with pytest.raises(InvalidTeamNameError):
        await _handler(uow).handle(CreateTeamAsAdmin(name=name, user_id=next_id()))

    assert uow.committed is False and uow.teams.teams == {}


async def test_only_the_new_team_id_is_returned():
    uow = FakeTeamsUnitOfWork()

    result = await _handler(uow).handle(CreateTeamAsAdmin(name="Atlas", user_id=next_id()))

    assert isinstance(result, UUID)
    assert set(uow.teams.teams) == {result}


async def test_by_default_every_team_gets_a_fresh_random_id():
    uow = FakeTeamsUnitOfWork()
    handler = CreateTeamAsAdminHandler(lambda: uow, FakeClock())

    first = await handler.handle(CreateTeamAsAdmin(name="Atlas", user_id=next_id()))
    second = await handler.handle(CreateTeamAsAdmin(name="Atlas", user_id=next_id()))

    assert first != second and first.version == 4
