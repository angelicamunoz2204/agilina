"""CreateTeam: the operator creates a team, with no author, in one transaction."""

import pytest

from agilina_api.teams.application.commands.create_team import CreateTeam, CreateTeamHandler
from agilina_api.teams.domain.errors import InvalidTeamNameError
from agilina_shared.enums import Language
from tests.api.builders import NOW
from tests.api.doubles import FakeClock, FakeTeamsUnitOfWork


async def test_the_operator_creates_a_team_without_an_author_and_it_is_committed():
    uow = FakeTeamsUnitOfWork()
    handler = CreateTeamHandler(lambda: uow, FakeClock())

    team_id = await handler.handle(CreateTeam(name="  Atlas  ", language=Language.ES))

    team = uow.teams.teams[team_id]
    assert team.name == "Atlas" and team.language is Language.ES
    assert team.created_by is None and team.created_at == NOW
    assert uow.committed is True


async def test_a_blank_name_is_refused_and_nothing_is_committed():
    uow = FakeTeamsUnitOfWork()

    with pytest.raises(InvalidTeamNameError):
        await CreateTeamHandler(lambda: uow, FakeClock()).handle(CreateTeam(name="   "))

    assert uow.committed is False and uow.teams.teams == {}
