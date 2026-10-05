"""In-memory doubles of the identity ports.

They implement the same ``Protocol`` as the real adapters, so a use case cannot tell them
apart; the real adapters are tested against PostgreSQL and Keycloak.
"""

import copy
from collections.abc import Callable
from datetime import datetime
from types import TracebackType
from typing import Self
from uuid import UUID

from agilina_api.identity.application.dtos import InvitationStatusView, TeamContacts
from agilina_api.identity.application.errors import (
    AccountAlreadyExistsError,
    IdentityProviderUnavailableError,
    PasswordPolicyError,
)
from agilina_api.identity.domain.invitation import Invitation, InvitationStatus
from agilina_api.identity.domain.user import AppUser
from agilina_api.identity.domain.value_objects import ActivationToken, Email, TokenHash
from agilina_shared.enums import TeamRole


class InMemoryInvitationRepository:
    """Stores and returns *copies*, like a database does: a change that is never saved is
    lost with the transaction, and a test cannot mistake it for persisted state."""

    def __init__(self) -> None:
        self.by_id: dict[UUID, Invitation] = {}
        self.saved: list[UUID] = []

    async def add(self, invitation: Invitation) -> None:
        from agilina_api.identity.domain.errors import PendingInvitationAlreadyExistsError

        for other in self.by_id.values():
            if (
                other.team_id == invitation.team_id
                and other.email == invitation.email
                and other.status is InvitationStatus.PENDING
            ):
                raise PendingInvitationAlreadyExistsError("pending already exists")
        self.by_id[invitation.id] = copy.deepcopy(invitation)

    async def save(self, invitation: Invitation) -> None:
        self.saved.append(invitation.id)
        self.by_id[invitation.id] = copy.deepcopy(invitation)

    async def get_by_token_hash(self, token_hash: TokenHash) -> Invitation | None:
        found = next((i for i in self.by_id.values() if i.token_hash == token_hash), None)
        return copy.deepcopy(found) if found is not None else None

    async def find_pending(self, team_id: UUID, email: Email) -> Invitation | None:
        found = next(
            (
                i
                for i in self.by_id.values()
                if i.team_id == team_id
                and i.email == email
                and i.status is InvitationStatus.PENDING
            ),
            None,
        )
        return copy.deepcopy(found) if found is not None else None


class InMemoryUserRepository:
    def __init__(self) -> None:
        self.users: list[AppUser] = []

    async def add(self, user: AppUser) -> None:
        self.users.append(user)

    async def get_by_email(self, email: Email) -> AppUser | None:
        return next((u for u in self.users if u.email == email), None)

    async def get_by_keycloak_subject(self, subject: str) -> AppUser | None:
        return next((u for u in self.users if u.keycloak_subject == subject), None)


class FakeTeamMembership:
    def __init__(self) -> None:
        self.added: list[tuple[UUID, UUID, TeamRole]] = []
        self.fail_with: Exception | None = None

    async def add_member(self, *, team_id: UUID, user_id: UUID, role: TeamRole) -> None:
        if self.fail_with is not None:
            raise self.fail_with
        self.added.append((team_id, user_id, role))


class FakeIdentityUnitOfWork:
    """One shared state, many ``async with`` blocks: what a commit stores is visible later."""

    def __init__(self) -> None:
        self.invitations = InMemoryInvitationRepository()
        self.users = InMemoryUserRepository()
        self.team_membership = FakeTeamMembership()
        self.commits = 0
        self.fail_on_commit: Exception | None = None

    def factory(self) -> Callable[[], Self]:
        return lambda: self

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        return None

    async def commit(self) -> None:
        if self.fail_on_commit is not None:
            raise self.fail_on_commit
        self.commits += 1

    async def rollback(self) -> None:
        return None


class FakeTokenGenerator:
    """Hands out known tokens, so a test can build the link it expects."""

    def __init__(self, *tokens: str) -> None:
        self._tokens = list(tokens) or ["A" * 43]
        self.generated: list[ActivationToken] = []

    def generate(self) -> ActivationToken:
        text = self._tokens[min(len(self.generated), len(self._tokens) - 1)]
        token = ActivationToken(text)
        self.generated.append(token)
        return token


class FakeIdentityProvider:
    def __init__(self) -> None:
        self.created: list[tuple[str, str, str]] = []
        self.deleted: list[str] = []
        self.error: Exception | None = None
        self.delete_error: Exception | None = None

    async def create_user(self, *, email: Email, full_name: str, password: str) -> str:
        if self.error is not None:
            raise self.error
        self.created.append((email.value, full_name, password))
        return f"kc-{len(self.created)}"

    async def delete_user(self, subject: str) -> None:
        if self.delete_error is not None:
            raise self.delete_error
        self.deleted.append(subject)

    # Shortcuts for the tests
    def refuse_password(self, *reasons: str) -> None:
        self.error = PasswordPolicyError(reasons)

    def already_has_the_account(self) -> None:
        self.error = AccountAlreadyExistsError("exists in Keycloak")

    def be_down(self) -> None:
        self.error = IdentityProviderUnavailableError("Keycloak does not answer")


class FakeInvitationQueries:
    """The read side over the same in-memory invitations the repository holds."""

    def __init__(self, invitations: InMemoryInvitationRepository) -> None:
        self._invitations = invitations

    async def get_status(self, token_hash: TokenHash, now: datetime) -> InvitationStatusView | None:
        invitation = await self._invitations.get_by_token_hash(token_hash)
        if invitation is None:
            return None
        return InvitationStatusView(
            email=invitation.email.value,
            full_name=invitation.full_name,
            role=invitation.role,
            status=invitation.state_at(now),
            expires_at=invitation.expires_at,
        )


class FakeTeamContactsDirectory:
    def __init__(self, contacts: dict[UUID, TeamContacts] | None = None) -> None:
        self.contacts = contacts or {}

    async def get(self, team_id: UUID) -> TeamContacts | None:
        return self.contacts.get(team_id)
