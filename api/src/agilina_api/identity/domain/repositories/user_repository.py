from typing import Protocol

from agilina_api.identity.domain.user import AppUser
from agilina_api.identity.domain.value_objects import Email


class UserRepository(Protocol):
    async def add(self, user: AppUser) -> None: ...

    async def get_by_email(self, email: Email) -> AppUser | None: ...

    async def get_by_keycloak_subject(self, subject: str) -> AppUser | None: ...
