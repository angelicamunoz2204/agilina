"""SQLAlchemy repository of the ``AppUser`` aggregate."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from agilina_api.identity.domain.errors import UserAlreadyExistsError
from agilina_api.identity.domain.repositories import UserRepository
from agilina_api.identity.domain.user import AppUser
from agilina_api.identity.domain.value_objects import Email
from agilina_api.identity.infrastructure.persistence.mappers import user_to_domain, user_to_row
from agilina_api.identity.infrastructure.persistence.orm_models import AppUserRow
from agilina_api.shared.infrastructure.database.types import violated_constraint

UNIQUE_CONSTRAINTS = {"app_user_email_key", "app_user_keycloak_subject_key"}


class SqlAlchemyUserRepository(UserRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, user: AppUser) -> None:
        self._session.add(user_to_row(user))
        try:
            await self._session.flush()
        except IntegrityError as error:
            if violated_constraint(error) in UNIQUE_CONSTRAINTS:
                raise UserAlreadyExistsError(
                    f"There is already an account for {user.email} or that Keycloak identity"
                ) from error
            raise

    async def get(self, user_id: UUID) -> AppUser | None:
        row = await self._session.get(AppUserRow, user_id)
        return user_to_domain(row) if row is not None else None

    async def get_by_email(self, email: Email) -> AppUser | None:
        statement = select(AppUserRow).where(AppUserRow.email == email.value)
        row = (await self._session.execute(statement)).scalar_one_or_none()
        return user_to_domain(row) if row is not None else None

    async def get_by_keycloak_subject(self, subject: str) -> AppUser | None:
        statement = select(AppUserRow).where(AppUserRow.keycloak_subject == subject)
        row = (await self._session.execute(statement)).scalar_one_or_none()
        return user_to_domain(row) if row is not None else None
