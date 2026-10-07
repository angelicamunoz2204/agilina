"""SQLAlchemy repository of the ``Sprint`` aggregate, with its participants."""

from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from agilina_api.teams.domain.repositories import SprintRepository
from agilina_api.teams.domain.sprint import Sprint
from agilina_api.teams.infrastructure.persistence.mappers import (
    participants_to_rows,
    sprint_to_domain,
    sprint_to_row,
)
from agilina_api.teams.infrastructure.persistence.orm_models import (
    SprintParticipantRow,
    SprintRow,
)
from agilina_api.teams.infrastructure.persistence.sprint_queries import (
    is_active_sprint_of,
    participants_of,
)


class SqlAlchemySprintRepository(SprintRepository):
    """It does not lock the sprint: every use case that changes one loads (and locks) its
    team first, so two changes to the same team's sprint never interleave."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, sprint: Sprint) -> None:
        self._session.add(sprint_to_row(sprint))
        await self._session.flush()  # the sprint row must exist before its participants
        self._session.add_all(participants_to_rows(sprint))
        await self._session.flush()

    async def get_active(self, team_id: UUID) -> Sprint | None:
        row = (
            await self._session.execute(select(SprintRow).where(is_active_sprint_of(team_id)))
        ).scalar_one_or_none()
        if row is None:
            return None
        return sprint_to_domain(row, await participants_of(self._session, row.id))

    async def save(self, sprint: Sprint) -> None:
        """Write the columns the aggregate knows and replace its participants.

        The participants are deleted and inserted again, in that order and in separate
        statements: rewriting the turn orders in place would collide with the
        ``(sprint_id, turn_order)`` unique constraint halfway through.
        """
        row = await self._session.get(SprintRow, sprint.id)
        if row is None:
            raise LookupError(f"Sprint {sprint.id} does not exist")
        row.start_date, row.end_date = sprint.period.start, sprint.period.end
        row.daily_time_utc = sprint.daily_time.at
        row.daily_time_zone = sprint.daily_time.time_zone
        row.status = sprint.status
        await self._session.execute(
            delete(SprintParticipantRow).where(SprintParticipantRow.sprint_id == sprint.id)
        )
        self._session.add_all(participants_to_rows(sprint))
        await self._session.flush()
