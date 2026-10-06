"""Storing builder-made objects in the real PostgreSQL, committed, as a test's starting data."""

from datetime import date
from uuid import UUID, uuid4

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from agilina_api.identity.domain.invitation import Invitation
from agilina_api.identity.domain.user import AppUser
from agilina_api.identity.infrastructure.persistence.invitation_repository import (
    SqlAlchemyInvitationRepository,
)
from agilina_api.identity.infrastructure.persistence.user_repository import SqlAlchemyUserRepository
from agilina_api.shared.infrastructure.database.unit_of_work import SqlAlchemyUnitOfWork
from agilina_api.teams.domain.sprint import SprintStatus
from agilina_api.teams.domain.team import Team
from agilina_api.teams.infrastructure.persistence.orm_models import SprintRow
from agilina_api.teams.infrastructure.persistence.team_repository import SqlAlchemyTeamRepository
from tests.api.builders import AppUserBuilder, InvitationBuilder, TeamBuilder

SessionFactory = async_sessionmaker[AsyncSession]


async def stored_team(session_factory: SessionFactory, builder: TeamBuilder | None = None) -> Team:
    """A committed team: invitations and memberships reference it. A removed member comes
    from ``TeamBuilder.with_removed_member``."""
    async with SqlAlchemyUnitOfWork(session_factory) as uow:
        team = await (builder or TeamBuilder()).saved_in(SqlAlchemyTeamRepository(uow.session))
        await uow.commit()
    return team


async def stored_user(
    session_factory: SessionFactory, builder: AppUserBuilder | None = None
) -> AppUser:
    """A committed user: an accepted invitation points to the person who used it."""
    async with SqlAlchemyUnitOfWork(session_factory) as uow:
        user = await (builder or AppUserBuilder().with_unique_email()).saved_in(
            SqlAlchemyUserRepository(uow.session)
        )
        await uow.commit()
    return user


async def stored_invitation(
    session_factory: SessionFactory, builder: InvitationBuilder
) -> Invitation:
    """A committed invitation (its team must already be stored)."""
    async with SqlAlchemyUnitOfWork(session_factory) as uow:
        invitation = await builder.saved_in(SqlAlchemyInvitationRepository(uow.session))
        await uow.commit()
    return invitation


async def stored_sprint(
    session_factory: SessionFactory, team_id: UUID, status: SprintStatus = SprintStatus.ACTIVE
) -> UUID:
    """A committed sprint of the team, with ``status``. There is no ``Sprint`` aggregate
    until HU-07, so the row is written straight in the table."""
    sprint_id = uuid4()
    async with session_factory() as session:
        session.add(
            SprintRow(
                id=sprint_id,
                team_id=team_id,
                start_date=date(2026, 10, 5),
                end_date=date(2026, 10, 16),
                status=status,
            )
        )
        await session.commit()
    return sprint_id
