"""Read side of teams (CQRS): straight SQL, no aggregate."""

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from agilina_api.teams.application.dtos import TeamSummary, TeamView, UserTeamView
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

    async def list_for_user(self, user_id: UUID) -> tuple[UserTeamView, ...]:
        # Served by the ``team_member_user_idx`` index on ``team_member.user_id``.
        statement = (
            select(TeamRow.id, TeamRow.name, TeamMemberRow.role)
            .join(TeamMemberRow, TeamMemberRow.team_id == TeamRow.id)
            .where(
                TeamMemberRow.user_id == user_id,
                TeamMemberRow.status == MembershipStatus.ACTIVE,
            )
            .order_by(func.lower(TeamRow.name), TeamRow.id)
        )
        async with self._session_factory() as session:
            rows = (await session.execute(statement)).all()
        return tuple(UserTeamView(team_id=row.id, name=row.name, role=row.role) for row in rows)

    async def get_team(self, team_id: UUID) -> TeamView | None:
        statement = select(TeamRow.id, TeamRow.name, TeamRow.mode, TeamRow.language).where(
            TeamRow.id == team_id
        )
        async with self._session_factory() as session:
            row = (await session.execute(statement)).one_or_none()
        if row is None:
            return None
        return TeamView(team_id=row.id, name=row.name, mode=row.mode, language=row.language)

    async def role_of(self, *, team_id: UUID, user_id: UUID) -> TeamRole | None:
        # At most one row, found through the unique index on ``(team_id, user_id)``.
        statement = select(TeamMemberRow.role).where(
            TeamMemberRow.team_id == team_id,
            TeamMemberRow.user_id == user_id,
            TeamMemberRow.status == MembershipStatus.ACTIVE,
        )
        async with self._session_factory() as session:
            role: TeamRole | None = (await session.execute(statement)).scalar_one_or_none()
        return role
