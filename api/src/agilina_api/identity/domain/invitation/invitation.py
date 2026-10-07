from datetime import datetime, timedelta
from uuid import UUID

from agilina_api.identity.domain.errors import (
    InvalidFullNameError,
    InvitationAlreadyUsedError,
    InvitationExpiredError,
    InvitationRevokedError,
)
from agilina_api.identity.domain.events import InvitationAccepted
from agilina_api.identity.domain.invitation.invitation_status import InvitationStatus
from agilina_api.identity.domain.value_objects import Email, TokenHash
from agilina_api.shared_kernel import AggregateRoot
from agilina_shared.enums import TeamRole

VALIDITY = timedelta(days=7)


def _require_utc(instant: datetime) -> datetime:
    if instant.tzinfo is None or instant.utcoffset() != timedelta(0):
        raise ValueError("Instants must be timezone-aware UTC (AD-20)")
    return instant


class Invitation(AggregateRoot[UUID]):
    def __init__(  # noqa: PLR0913 - an aggregate carries its whole state
        self,
        *,
        invitation_id: UUID,
        team_id: UUID,
        email: Email,
        full_name: str,
        role: TeamRole,
        token_hash: TokenHash,
        status: InvitationStatus,
        expires_at: datetime,
        created_by: UUID | None,
        created_at: datetime,
        accepted_at: datetime | None = None,
        accepted_user_id: UUID | None = None,
    ) -> None:
        super().__init__(invitation_id)
        self._team_id = team_id
        self._email = email
        self._full_name = full_name
        self._role = role
        self._token_hash = token_hash
        self._status = status
        self._expires_at = expires_at
        self._created_by = created_by
        self._created_at = created_at
        self._accepted_at = accepted_at
        self._accepted_user_id = accepted_user_id

    # ------------------------------------------------------------- creation --
    @classmethod
    def issue(  # noqa: PLR0913
        cls,
        *,
        invitation_id: UUID,
        team_id: UUID,
        email: Email,
        full_name: str,
        role: TeamRole,
        token_hash: TokenHash,
        created_by: UUID | None,
        now: datetime,
    ) -> "Invitation":
        """A new pending invitation.

        ``created_by`` is the team member who issued it, or ``None`` when the platform
        operator did, to create a team's first admin (AD-22).
        """
        _require_utc(now)
        name = full_name.strip()
        if not name:
            raise InvalidFullNameError("A person's name cannot be blank")
        return cls(
            invitation_id=invitation_id,
            team_id=team_id,
            email=email,
            full_name=name,
            role=role,
            token_hash=token_hash,
            status=InvitationStatus.PENDING,
            expires_at=now + VALIDITY,
            created_by=created_by,
            created_at=now,
        )

    # ------------------------------------------------------------ read state --
    @property
    def team_id(self) -> UUID:
        return self._team_id

    @property
    def email(self) -> Email:
        return self._email

    @property
    def full_name(self) -> str:
        return self._full_name

    @property
    def role(self) -> TeamRole:
        return self._role

    @property
    def token_hash(self) -> TokenHash:
        return self._token_hash

    @property
    def status(self) -> InvitationStatus:
        """The stored status. It says ``pending`` for an expired link nobody has touched
        yet: ask ``state_at`` for what is true now."""
        return self._status

    @property
    def expires_at(self) -> datetime:
        return self._expires_at

    @property
    def created_by(self) -> UUID | None:
        return self._created_by

    @property
    def created_at(self) -> datetime:
        return self._created_at

    @property
    def accepted_at(self) -> datetime | None:
        return self._accepted_at

    @property
    def accepted_user_id(self) -> UUID | None:
        return self._accepted_user_id

    def state_at(self, now: datetime) -> InvitationStatus:
        """What the invitation is at ``now``: a pending one past its deadline is expired."""
        _require_utc(now)
        if self._status is InvitationStatus.PENDING and now >= self._expires_at:
            return InvitationStatus.EXPIRED
        return self._status

    # -------------------------------------------------------------- behavior --
    def accept(self, *, user_id: UUID, now: datetime) -> None:
        """Mark the invitation as used by ``user_id``; fails if it can no longer be."""
        state = self.state_at(now)
        if state is InvitationStatus.ACCEPTED:
            raise InvitationAlreadyUsedError(self.id, state, now)
        if state is InvitationStatus.EXPIRED:
            raise InvitationExpiredError(self.id, state, now)
        if state is InvitationStatus.REVOKED:
            raise InvitationRevokedError(self.id, state, now)

        self._status = InvitationStatus.ACCEPTED
        self._accepted_at = now
        self._accepted_user_id = user_id
        self._record(
            InvitationAccepted(
                occurred_at=now,
                invitation_id=self.id,
                team_id=self._team_id,
                user_id=user_id,
                email=self._email,
                role=self._role,
            )
        )

    def expire_if_due(self, now: datetime) -> bool:
        """Store the expiry of a pending invitation whose deadline passed.

        Returns whether it changed. Expiry is always *computed* by ``state_at``; this only
        lets a caller persist it so the stored status stops saying ``pending``.
        """
        if (
            self.state_at(now) is InvitationStatus.EXPIRED
            and self._status is not InvitationStatus.EXPIRED
        ):
            self._status = InvitationStatus.EXPIRED
            return True
        return False
