"""One team, for the members who open it (HU-05: the team's dashboard)."""

from dataclasses import dataclass
from uuid import UUID

from agilina_api.teams.application.dtos import TeamView
from agilina_api.teams.application.ports.outbound import TeamQueries
from agilina_api.teams.domain.errors import TeamNotFoundError


@dataclass(frozen=True)
class GetTeam:
    team_id: UUID


class GetTeamHandler:
    """It does not check who asks: the route lets only the team's members get here."""

    def __init__(self, queries: TeamQueries) -> None:
        self._queries = queries

    async def handle(self, query: GetTeam) -> TeamView:
        view = await self._queries.get_team(query.team_id)
        if view is None:
            raise TeamNotFoundError(f"Team {query.team_id} does not exist")
        return view
