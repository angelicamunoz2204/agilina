from agilina_api.teams.application.dtos import TeamView
from agilina_api.teams.application.ports.outbound import TeamQueries
from agilina_api.teams.application.queries.get_team.get_team import GetTeam
from agilina_api.teams.domain.errors import TeamNotFoundError


class GetTeamHandler:
    """It does not check who asks: the route lets only the team's members get here."""

    def __init__(self, queries: TeamQueries) -> None:
        self._queries = queries

    async def handle(self, query: GetTeam) -> TeamView:
        view = await self._queries.get_team(query.team_id)
        if view is None:
            raise TeamNotFoundError(f"Team {query.team_id} does not exist")
        return view
