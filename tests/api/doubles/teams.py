"""In-memory doubles of the teams ports."""

from types import TracebackType
from typing import Self
from uuid import UUID

from agilina_api.teams.domain.team import Team


class InMemoryTeamRepository:
    def __init__(self) -> None:
        self.teams: dict[UUID, Team] = {}
        self.saved: list[UUID] = []

    async def add(self, team: Team) -> None:
        self.teams[team.id] = team

    async def get(self, team_id: UUID) -> Team | None:
        return self.teams.get(team_id)

    async def save(self, team: Team) -> None:
        self.saved.append(team.id)
        self.teams[team.id] = team


class FakeTeamsUnitOfWork:
    def __init__(self, teams: InMemoryTeamRepository | None = None) -> None:
        self.teams = teams or InMemoryTeamRepository()
        self.committed = False

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        return None

    async def commit(self) -> None:
        self.committed = True

    async def rollback(self) -> None:
        self.committed = False
