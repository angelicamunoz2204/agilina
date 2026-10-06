"""The one question about sprints HU-06 asks: does the team have one in progress?"""

from uuid import UUID

from sqlalchemy import exists, select
from sqlalchemy.ext.asyncio import AsyncSession

from agilina_api.teams.application.ports.outbound import ActiveSprints
from agilina_api.teams.domain.sprint import SprintStatus
from agilina_api.teams.infrastructure.persistence.orm_models import SprintRow


async def team_has_active_sprint(session: AsyncSession, team_id: UUID) -> bool:
    """Whether the team has a sprint with status ``active``, read in ``session``.

    The single place that answers it: the role change asks it inside its transaction
    (``SqlActiveSprints``) and the members list inside its read (``SqlTeamQueries``). The
    ``sprint_one_active_per_team`` index keeps it to one row at most.
    """
    statement = select(
        exists().where(SprintRow.team_id == team_id, SprintRow.status == SprintStatus.ACTIVE)
    )
    return bool((await session.execute(statement)).scalar_one())


class SqlActiveSprints(ActiveSprints):
    """``ActiveSprints`` inside a unit of work: it reads in the transaction's session."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def has_active_sprint(self, team_id: UUID) -> bool:
        return await team_has_active_sprint(self._session, team_id)
