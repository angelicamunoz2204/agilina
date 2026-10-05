"""Read side of teams (CQRS): straight SQL, no aggregate."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from agilina_api.teams.application.dtos import TeamSummary
from agilina_api.teams.application.ports.outbound import TeamQueries
from agilina_api.teams.domain.team import MembershipStatus
from agilina_api.teams.infrastructure.persistence.orm_models import TeamMemberRow, TeamRow
from agilina_shared.enums import TeamRole


class SqlTeamQueries(TeamQueries):
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def get_summary(self, team_id: UUID) -> TeamSummary | None:
        async with self._session_factory() as session:
            team = (
                await session.execute(
                    select(TeamRow.id, TeamRow.name, TeamRow.language).where(TeamRow.id == team_id)
                )
            ).one_or_none()
            if team is None:
                return None
            admins = (
                await session.execute(
                    select(TeamMemberRow.user_id)
                    .where(
                        TeamMemberRow.team_id == team_id,
                        TeamMemberRow.role == TeamRole.ADMIN,
                        TeamMemberRow.status == MembershipStatus.ACTIVE,
                    )
                    .order_by(TeamMemberRow.joined_at)
                )
            ).scalars()
            return TeamSummary(
                team_id=team.id,
                name=team.name,
                language=team.language,
                admin_user_ids=tuple(admins),
            )
