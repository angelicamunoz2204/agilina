"""SQLAlchemy repository of the ``Invitation`` aggregate (the write side)."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from agilina_api.identity.domain.errors import PendingInvitationAlreadyExistsError
from agilina_api.identity.domain.invitation import Invitation, InvitationStatus
from agilina_api.identity.domain.repositories import InvitationRepository
from agilina_api.identity.domain.value_objects import Email, TokenHash
from agilina_api.identity.infrastructure.persistence.mappers import (
    invitation_to_domain,
    invitation_to_row,
)
from agilina_api.identity.infrastructure.persistence.orm_models import InvitationRow
from agilina_api.shared.infrastructure.database.types import violated_constraint

PENDING_UNIQUE = "invitation_pending_unique"


class SqlAlchemyInvitationRepository(InvitationRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, invitation: Invitation) -> None:
        self._session.add(invitation_to_row(invitation))
        try:
            await self._session.flush()
        except IntegrityError as error:
            if violated_constraint(error) == PENDING_UNIQUE:
                raise PendingInvitationAlreadyExistsError(
                    f"Team {invitation.team_id} already has a pending invitation "
                    f"for {invitation.email}"
                ) from error
            raise

    async def save(self, invitation: Invitation) -> None:
        row = await self._session.get(InvitationRow, invitation.id)
        if row is None:
            raise LookupError(f"Invitation {invitation.id} does not exist")
        # Only what can change after issuing: the rest of the row is left as it is.
        row.status = invitation.status
        row.accepted_at = invitation.accepted_at
        row.accepted_user_id = invitation.accepted_user_id
        await self._session.flush()

    async def get_by_token_hash(self, token_hash: TokenHash) -> Invitation | None:
        """Look an invitation up by its token and **lock its row** until the transaction ends.

        The lock is what makes two simultaneous activations of the same link safe: the
        second waits for the first and then finds the invitation already used.
        """
        statement = (
            select(InvitationRow)
            .where(InvitationRow.token_hash == token_hash.value)
            .with_for_update()
        )
        row = (await self._session.execute(statement)).scalar_one_or_none()
        return invitation_to_domain(row) if row is not None else None

    async def find_pending(self, team_id: UUID, email: Email) -> Invitation | None:
        """The invitation *stored* as pending for that email in that team.

        It may already be past its deadline: stored status and real state differ until
        someone calls ``expire_if_due`` and saves. Issuing a new invitation to the same
        email must do that first, or the unique index on pending invitations refuses it.
        """
        statement = select(InvitationRow).where(
            InvitationRow.team_id == team_id,
            InvitationRow.email == email.value,
            InvitationRow.status == InvitationStatus.PENDING,
        )
        row = (await self._session.execute(statement)).scalar_one_or_none()
        return invitation_to_domain(row) if row is not None else None
