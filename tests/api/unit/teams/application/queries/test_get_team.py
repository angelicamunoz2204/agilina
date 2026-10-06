"""GetTeam: one team, for the members who open its dashboard."""

import pytest

from agilina_api.teams.application.dtos import TeamView
from agilina_api.teams.application.queries.get_team import GetTeam, GetTeamHandler
from agilina_api.teams.domain.errors import TeamNotFoundError
from agilina_shared.enums import Language, OperationMode
from tests.api.builders import next_id
from tests.api.doubles import FakeTeamQueries


async def test_it_returns_the_name_mode_and_language_of_the_team():
    team_id = next_id()
    view = TeamView(team_id=team_id, name="Atlas", mode=OperationMode.SUPPORT, language=Language.EN)
    handler = GetTeamHandler(FakeTeamQueries(views={team_id: view}))

    assert await handler.handle(GetTeam(team_id=team_id)) == view


async def test_a_team_that_does_not_exist_is_not_found():
    handler = GetTeamHandler(FakeTeamQueries())

    with pytest.raises(TeamNotFoundError):
        await handler.handle(GetTeam(team_id=next_id()))
