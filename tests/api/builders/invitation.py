"""Builder of ``Invitation``."""

from dataclasses import dataclass, field, replace
from datetime import datetime, timedelta
from typing import Protocol, Self
from uuid import UUID

from agilina_api.identity.domain.invitation import VALIDITY, Invitation, InvitationStatus
from agilina_api.identity.domain.value_objects import ActivationToken, Email
from agilina_shared.enums import TeamRole
from tests.api.builders.defaults import EMAIL, FULL_NAME, NOW, TOKEN
from tests.api.builders.identifiers import next_id


@dataclass(frozen=True)
class InvitationBuilder:
    """A pending invitation for ``julian@example.test``, issued at ``NOW`` and valid for
    seven days. ``token`` is the text the invited person would receive."""

    invitation_id: UUID = field(default_factory=next_id)
    team_id: UUID = field(default_factory=next_id)
    email: str = EMAIL
    full_name: str = FULL_NAME
    role: TeamRole = TeamRole.MEMBER
    token: str = TOKEN
    created_by: UUID | None = None
    issued_at: datetime = NOW
    accepted_by_user: UUID | None = None
    marked_expired: bool = False
    marked_revoked: bool = False
    restored_status: InvitationStatus | None = None

    # ---------------------------------------------------------------- data --
    def with_id(self, invitation_id: UUID) -> Self:
        return replace(self, invitation_id=invitation_id)

    def for_team(self, team_id: UUID) -> Self:
        return replace(self, team_id=team_id)

    def with_email(self, email: str) -> Self:
        return replace(self, email=email)

    def named(self, full_name: str) -> Self:
        return replace(self, full_name=full_name)

    def as_admin(self) -> Self:
        return replace(self, role=TeamRole.ADMIN)

    def as_member(self) -> Self:
        return replace(self, role=TeamRole.MEMBER)

    def with_token(self, token: str) -> Self:
        return replace(self, token=token)

    def with_unique_token(self) -> Self:
        """A token no other builder produces: the database refuses two invitations that
        share one (``token_hash`` is unique)."""
        return replace(self, token=f"{self.invitation_id.int:043d}")

    def created_by_user(self, user_id: UUID | None) -> Self:
        return replace(self, created_by=user_id)

    def issued_at_instant(self, instant: datetime) -> Self:
        return replace(self, issued_at=instant)

    # --------------------------------------------------------------- states --
    def accepted_by(self, user_id: UUID) -> Self:
        """Used: the invitation was accepted (one hour after it was issued)."""
        return replace(self, accepted_by_user=user_id)

    def past_its_deadline(self) -> Self:
        """Issued so long ago that, at ``NOW``, its seven days have run out. Its stored
        status stays pending until something marks it, as in production."""
        return replace(self, issued_at=NOW - VALIDITY - timedelta(seconds=1))

    def expired(self) -> Self:
        """Past its deadline and already marked as expired."""
        return replace(self.past_its_deadline(), marked_expired=True)

    def revoked(self) -> Self:
        """Replaced by a newer invitation to the same person (one hour after it was
        issued), through ``Invitation.revoke``."""
        return replace(self, marked_revoked=True)

    def restored_as(self, status: InvitationStatus) -> Self:
        """Rebuilt from storage in ``status`` as is, without going through the domain's
        rules: for a stored state no behavior reaches."""
        return replace(self, restored_status=status)

    # ---------------------------------------------------------------- build --
    @property
    def activation_token(self) -> ActivationToken:
        return ActivationToken(self.token)

    def build(self) -> Invitation:
        if self.restored_status is not None:
            return Invitation(
                invitation_id=self.invitation_id,
                team_id=self.team_id,
                email=Email(self.email),
                full_name=self.full_name,
                role=self.role,
                token_hash=self.activation_token.hash(),
                status=self.restored_status,
                expires_at=self.issued_at + VALIDITY,
                created_by=self.created_by,
                created_at=self.issued_at,
            )
        invitation = Invitation.issue(
            invitation_id=self.invitation_id,
            team_id=self.team_id,
            email=Email(self.email),
            full_name=self.full_name,
            role=self.role,
            token_hash=self.activation_token.hash(),
            created_by=self.created_by,
            now=self.issued_at,
        )
        if self.accepted_by_user is not None:
            invitation.accept(
                user_id=self.accepted_by_user, now=self.issued_at + timedelta(hours=1)
            )
        if self.marked_expired:
            invitation.expire_if_due(NOW)
        if self.marked_revoked:
            invitation.revoke(self.issued_at + timedelta(hours=1))
        invitation.pull_events()
        return invitation

    async def saved_in(self, repository: "InvitationStore") -> Invitation:
        invitation = self.build()
        await repository.add(invitation)
        return invitation


class InvitationStore(Protocol):
    """What ``saved_in`` needs from a repository (both the in-memory and the SQL one)."""

    async def add(self, invitation: Invitation) -> None: ...
