"""In-memory doubles of the teams ports."""

from types import TracebackType
from typing import Self
from uuid import UUID

from agilina_api.teams.application.dtos import TeamSummary, TeamView, UserTeamView
from agilina_api.teams.domain.team import Team
from agilina_shared.enums import TeamRole


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


class FakeTeamQueries:
    """Answers with what the test gives it: summaries and views by team, teams by user
    and roles by team and user."""

    def __init__(
        self,
        summaries: dict[UUID, TeamSummary] | None = None,
        teams_by_user: dict[UUID, tuple[UserTeamView, ...]] | None = None,
        views: dict[UUID, TeamView] | None = None,
        roles: dict[tuple[UUID, UUID], TeamRole] | None = None,
    ) -> None:
        self.summaries = summaries or {}
        self.teams_by_user = teams_by_user or {}
        self.views = views or {}
        self.roles = roles or {}

    async def get_summary(self, team_id: UUID) -> TeamSummary | None:
        return self.summaries.get(team_id)

    async def list_for_user(self, user_id: UUID) -> tuple[UserTeamView, ...]:
        return self.teams_by_user.get(user_id, ())

    async def get_team(self, team_id: UUID) -> TeamView | None:
        return self.views.get(team_id)

    async def role_of(self, *, team_id: UUID, user_id: UUID) -> TeamRole | None:
        return self.roles.get((team_id, user_id))
