"""ListMyTeams: the teams of a user, for the team selector (acceptance criterion 5)."""

from agilina_api.teams.application.dtos import UserTeamView
from agilina_api.teams.application.queries.list_my_teams import ListMyTeams, ListMyTeamsHandler
from agilina_shared.enums import OperationMode, TeamRole
from tests.api.builders import next_id
from tests.api.doubles import FakeTeamQueries


async def test_it_returns_every_team_of_the_user_with_its_role():
    ana, bruno = next_id(), next_id()
    teams_of_ana = (
        UserTeamView(
            team_id=next_id(), name="Atlas", role=TeamRole.ADMIN, mode=OperationMode.SUPPORT
        ),
        UserTeamView(
            team_id=next_id(), name="Boreal", role=TeamRole.MEMBER, mode=OperationMode.SUPPORT
        ),
    )
    queries = FakeTeamQueries(
        teams_by_user={
            ana: teams_of_ana,
            bruno: (
                UserTeamView(
                    team_id=next_id(), name="Cielo", role=TeamRole.ADMIN, mode=OperationMode.SUPPORT
                ),
            ),
        }
    )

    assert await ListMyTeamsHandler(queries).handle(ListMyTeams(user_id=ana)) == teams_of_ana


async def test_a_user_without_teams_gets_none():
    handler = ListMyTeamsHandler(FakeTeamQueries())

    assert await handler.handle(ListMyTeams(user_id=next_id())) == ()
