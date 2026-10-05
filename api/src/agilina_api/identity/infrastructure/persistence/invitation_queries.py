"""Read side of invitations (CQRS): straight SQL, no aggregate and no repository."""

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from agilina_api.identity.application.dtos import InvitationStatusView
from agilina_api.identity.application.ports.outbound import InvitationQueries
from agilina_api.identity.domain.invitation import InvitationStatus
from agilina_api.identity.domain.value_objects import TokenHash
from agilina_api.identity.infrastructure.persistence.orm_models import InvitationRow


class SqlInvitationQueries(InvitationQueries):
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def get_status(self, token_hash: TokenHash, now: datetime) -> InvitationStatusView | None:
        statement = select(
            InvitationRow.email,
            InvitationRow.full_name,
            InvitationRow.role,
            InvitationRow.status,
            InvitationRow.expires_at,
        ).where(InvitationRow.token_hash == token_hash.value)
        async with self._session_factory() as session:
            row = (await session.execute(statement)).one_or_none()
        if row is None:
            return None
        # The same rule as ``Invitation.state_at``: a pending one past its deadline is expired.
        overdue = row.status is InvitationStatus.PENDING and now >= row.expires_at
        return InvitationStatusView(
            email=row.email,
            full_name=row.full_name,
            role=row.role,
            status=InvitationStatus.EXPIRED if overdue else row.status,
            expires_at=row.expires_at,
        )
