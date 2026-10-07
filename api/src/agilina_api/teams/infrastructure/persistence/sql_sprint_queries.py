"""Read side of the sprint (CQRS): the team's active sprint, straight SQL, no aggregate."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from agilina_api.teams.application.dtos import ActiveSprintRecord
from agilina_api.teams.application.ports.outbound import SprintQueries
from agilina_api.teams.infrastructure.persistence.orm_models import SprintRow
from agilina_api.teams.infrastructure.persistence.sprint_queries import (
    is_active_sprint_of,
    participants_of,
)


class SqlSprintQueries(SprintQueries):
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def active_sprint_of(self, team_id: UUID) -> ActiveSprintRecord | None:
        statement = select(
            SprintRow.id,
            SprintRow.start_date,
            SprintRow.end_date,
            SprintRow.daily_time_utc,
            SprintRow.daily_time_zone,
        ).where(is_active_sprint_of(team_id))
        async with self._session_factory() as session:
            row = (await session.execute(statement)).one_or_none()
            if row is None:
                return None
            participants = await participants_of(session, row.id)
        return ActiveSprintRecord(
            sprint_id=row.id,
            start_date=row.start_date,
            end_date=row.end_date,
            daily_time=row.daily_time_utc,
            time_zone=row.daily_time_zone,
            participants=participants,
        )
