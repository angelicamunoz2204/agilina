"""The questions about a team's active sprint, all answered with one predicate: whether it
has one (HU-06 asks it through ``SqlActiveSprints``) and which one it is (HU-07: the
repository and ``SqlSprintQueries``)."""

from uuid import UUID

from sqlalchemy import ColumnElement, and_, exists, select
from sqlalchemy.ext.asyncio import AsyncSession

from agilina_api.teams.application.ports.outbound import ActiveSprints
from agilina_api.teams.domain.sprint import SprintStatus
from agilina_api.teams.infrastructure.persistence.orm_models import (
    SprintParticipantRow,
    SprintRow,
)


def is_active_sprint_of(team_id: UUID) -> ColumnElement[bool]:
    """The ``sprint`` row is the team's active one. The single definition of "the team's
    active sprint": ``team_has_active_sprint``, the repository and ``SqlSprintQueries`` use
    it. The ``sprint_one_active_per_team`` index keeps it to one row at most."""
    return and_(SprintRow.team_id == team_id, SprintRow.status == SprintStatus.ACTIVE)


async def team_has_active_sprint(session: AsyncSession, team_id: UUID) -> bool:
    """Whether the team has a sprint with status ``active``, read in ``session``.

    The single place that answers it: the role change asks it inside its transaction
    (``SqlActiveSprints``) and the members list inside its read (``SqlTeamQueries``).
    """
    statement = select(exists().where(is_active_sprint_of(team_id)))
    return bool((await session.execute(statement)).scalar_one())


async def participants_of(session: AsyncSession, sprint_id: UUID) -> tuple[UUID, ...]:
    """The ``user_id`` of the sprint's participants, in turn order, read in ``session``."""
    statement = (
        select(SprintParticipantRow.user_id)
        .where(SprintParticipantRow.sprint_id == sprint_id)
        .order_by(SprintParticipantRow.turn_order)
    )
    return tuple((await session.execute(statement)).scalars())


class SqlActiveSprints(ActiveSprints):
    """``ActiveSprints`` inside a unit of work: it reads in the transaction's session."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def has_active_sprint(self, team_id: UUID) -> bool:
        return await team_has_active_sprint(self._session, team_id)
