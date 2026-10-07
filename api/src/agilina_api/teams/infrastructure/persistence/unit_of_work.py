"""Unit of work of the teams commands: a transaction with the repositories and the sprint
question, all on the transaction's session."""

from collections.abc import Callable
from typing import Self

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from agilina_api.shared.infrastructure.database.unit_of_work import SqlAlchemyUnitOfWork
from agilina_api.teams.application.ports.outbound import ActiveSprints
from agilina_api.teams.domain.repositories import SprintRepository, TeamRepository
from agilina_api.teams.infrastructure.persistence.sprint_queries import SqlActiveSprints
from agilina_api.teams.infrastructure.persistence.sprint_repository import (
    SqlAlchemySprintRepository,
)
from agilina_api.teams.infrastructure.persistence.team_repository import SqlAlchemyTeamRepository


class SqlAlchemyTeamsUnitOfWork(SqlAlchemyUnitOfWork):
    teams: TeamRepository
    sprints: SprintRepository
    active_sprints: ActiveSprints

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        super().__init__(session_factory)

    async def __aenter__(self) -> Self:
        await super().__aenter__()
        self.teams = SqlAlchemyTeamRepository(self.session)
        self.sprints = SqlAlchemySprintRepository(self.session)
        self.active_sprints = SqlActiveSprints(self.session)
        return self


def teams_unit_of_work_factory(
    session_factory: async_sessionmaker[AsyncSession],
) -> Callable[[], SqlAlchemyTeamsUnitOfWork]:
    return lambda: SqlAlchemyTeamsUnitOfWork(session_factory)
