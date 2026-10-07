from agilina_api.teams.application.dtos import UserTeamView
from agilina_api.teams.application.ports.outbound import TeamQueries
from agilina_api.teams.application.queries.list_my_teams.list_my_teams import ListMyTeams


class ListMyTeamsHandler:
    def __init__(self, queries: TeamQueries) -> None:
        self._queries = queries

    async def handle(self, query: ListMyTeams) -> tuple[UserTeamView, ...]:
        """Only active memberships: a team the user was removed from is not theirs."""
        return await self._queries.list_for_user(query.user_id)
