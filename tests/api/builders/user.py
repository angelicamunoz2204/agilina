"""Builder of ``AppUser``."""

from dataclasses import dataclass, field, replace
from datetime import datetime
from typing import Protocol, Self
from uuid import UUID

from agilina_api.identity.domain.user import AppUser
from agilina_api.identity.domain.value_objects import Email
from tests.api.builders.defaults import EMAIL, FULL_NAME, NOW
from tests.api.builders.identifiers import next_id


@dataclass(frozen=True)
class AppUserBuilder:
    """An active user registered at ``NOW``, with a Keycloak subject derived from its id
    (so two users never share one)."""

    user_id: UUID = field(default_factory=next_id)
    keycloak_subject: str | None = None
    email: str = EMAIL
    full_name: str = FULL_NAME
    registered_at: datetime = NOW
    active: bool = True

    def with_id(self, user_id: UUID) -> Self:
        return replace(self, user_id=user_id)

    def with_subject(self, keycloak_subject: str) -> Self:
        return replace(self, keycloak_subject=keycloak_subject)

    def with_email(self, email: str) -> Self:
        return replace(self, email=email)

    def with_unique_email(self) -> Self:
        """An address no other user has: the database refuses repeats (it is ``CITEXT UNIQUE``)."""
        return replace(self, email=f"user-{self.user_id.int}@example.test")

    def named(self, full_name: str) -> Self:
        return replace(self, full_name=full_name)

    def registered_at_instant(self, instant: datetime) -> Self:
        return replace(self, registered_at=instant)

    def disabled(self) -> Self:
        """An account that can no longer sign in. No behavior disables an account yet, so
        it is rebuilt as stored, like ``InvitationBuilder.restored_as``."""
        return replace(self, active=False)

    def build(self) -> AppUser:
        if not self.active:
            return AppUser(
                user_id=self.user_id,
                keycloak_subject=self.keycloak_subject or f"subject-{self.user_id}",
                email=Email(self.email),
                full_name=self.full_name,
                is_active=False,
                created_at=self.registered_at,
            )
        user = AppUser.register(
            user_id=self.user_id,
            keycloak_subject=self.keycloak_subject or f"subject-{self.user_id}",
            email=Email(self.email),
            full_name=self.full_name,
            now=self.registered_at,
        )
        user.pull_events()
        return user

    async def saved_in(self, repository: "UserStore") -> AppUser:
        user = self.build()
        await repository.add(user)
        return user


class UserStore(Protocol):
    async def add(self, user: AppUser) -> None: ...
