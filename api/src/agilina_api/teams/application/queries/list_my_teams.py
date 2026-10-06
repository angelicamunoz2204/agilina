"""The teams a user belongs to, for the team selector (HU-05, acceptance criterion 5)."""

from dataclasses import dataclass
from uuid import UUID

from agilina_api.teams.application.dtos import UserTeamView
from agilina_api.teams.application.ports.outbound import TeamQueries


@dataclass(frozen=True)
class ListMyTeams:
    user_id: UUID


class ListMyTeamsHandler:
    def __init__(self, queries: TeamQueries) -> None:
        self._queries = queries

    async def handle(self, query: ListMyTeams) -> tuple[UserTeamView, ...]:
        """Only active memberships: a team the user was removed from is not theirs."""
        return await self._queries.list_for_user(query.user_id)
