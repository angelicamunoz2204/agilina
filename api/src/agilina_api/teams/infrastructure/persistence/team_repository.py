"""SQLAlchemy repository of the ``Team`` aggregate, with its memberships."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from agilina_api.teams.domain.repositories import TeamRepository
from agilina_api.teams.domain.team import Membership, Team
from agilina_api.teams.infrastructure.persistence.orm_models import TeamMemberRow, TeamRow


class SqlAlchemyTeamRepository(TeamRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, team: Team) -> None:
        self._session.add(
            TeamRow(
                id=team.id,
                name=team.name,
                mode=team.mode,
                language=team.language,
                created_by=team.created_by,
                created_at=team.created_at,
            )
        )
        await self._session.flush()  # the team row must exist before its members
        for membership in team.memberships:
            self._session.add(self._member_row(team.id, membership))
        await self._session.flush()

    async def get(self, team_id: UUID) -> Team | None:
        """Load the team with its memberships and **lock its row** until the transaction
        ends.

        The lock serializes every change to the team's members (a role change, a removal,
        an activation that adds a member): two admins demoting each other at the same time
        would otherwise each see the other still admin and leave the team without one. The
        second waits for the first and then reads the memberships it committed.
        """
        row = (
            await self._session.execute(
                select(TeamRow).where(TeamRow.id == team_id).with_for_update()
            )
        ).scalar_one_or_none()
        if row is None:
            return None
        members = (
            await self._session.execute(
                select(TeamMemberRow).where(TeamMemberRow.team_id == team_id)
            )
        ).scalars()
        return Team(
            team_id=row.id,
            name=row.name,
            mode=row.mode,
            language=row.language,
            created_by=row.created_by,
            created_at=row.created_at,
            memberships=[
                Membership(
                    membership_id=m.id,
                    user_id=m.user_id,
                    role=m.role,
                    status=m.status,
                    joined_at=m.joined_at,
                    removed_at=m.removed_at,
                )
                for m in members
            ],
        )

    async def save(self, team: Team) -> None:
        row = await self._session.get(TeamRow, team.id)
        if row is None:
            raise LookupError(f"Team {team.id} does not exist")
        row.name, row.mode, row.language = team.name, team.mode, team.language

        stored = {
            m.id: m
            for m in (
                await self._session.execute(
                    select(TeamMemberRow).where(TeamMemberRow.team_id == team.id)
                )
            ).scalars()
        }
        for membership in team.memberships:
            current = stored.get(membership.id)
            if current is None:
                self._session.add(self._member_row(team.id, membership))
            else:
                current.role = membership.role
                current.status = membership.status
                current.joined_at = membership.joined_at
                current.removed_at = membership.removed_at
        await self._session.flush()

    @staticmethod
    def _member_row(team_id: UUID, membership: Membership) -> TeamMemberRow:
        return TeamMemberRow(
            id=membership.id,
            team_id=team_id,
            user_id=membership.user_id,
            role=membership.role,
            status=membership.status,
            joined_at=membership.joined_at,
            removed_at=membership.removed_at,
        )
