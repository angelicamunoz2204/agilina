"""Unit of work of the identity commands: one transaction with its repositories."""

from collections.abc import Callable
from typing import Self

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from agilina_api.identity.application.ports.outbound import TeamMembership
from agilina_api.identity.domain.repositories import InvitationRepository, UserRepository
from agilina_api.identity.infrastructure.persistence.invitation_repository import (
    SqlAlchemyInvitationRepository,
)
from agilina_api.identity.infrastructure.persistence.user_repository import SqlAlchemyUserRepository
from agilina_api.shared.infrastructure.database.unit_of_work import SqlAlchemyUnitOfWork


class SqlAlchemyIdentityUnitOfWork(SqlAlchemyUnitOfWork):
    invitations: InvitationRepository
    users: UserRepository
    team_membership: TeamMembership

    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        team_membership_factory: Callable[[AsyncSession], TeamMembership],
    ) -> None:
        super().__init__(session_factory)
        self._team_membership_factory = team_membership_factory

    async def __aenter__(self) -> Self:
        await super().__aenter__()
        session = self.session
        self.invitations = SqlAlchemyInvitationRepository(session)
        self.users = SqlAlchemyUserRepository(session)
        # Built on the same session: adding the member is part of this transaction.
        self.team_membership = self._team_membership_factory(session)
        return self


def identity_unit_of_work_factory(
    session_factory: async_sessionmaker[AsyncSession],
    team_membership_factory: Callable[[AsyncSession], TeamMembership],
) -> Callable[[], SqlAlchemyIdentityUnitOfWork]:
    return lambda: SqlAlchemyIdentityUnitOfWork(session_factory, team_membership_factory)
