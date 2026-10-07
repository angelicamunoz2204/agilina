"""Read side: who to e-mail among a set of users (CQRS)."""

from collections.abc import Collection
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from agilina_api.identity.application.dtos import Contact
from agilina_api.identity.domain.value_objects import Email
from agilina_api.identity.infrastructure.persistence.orm_models import AppUserRow


class SqlUserContacts:
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def get_contacts(self, user_ids: Collection[UUID]) -> list[Contact]:
        if not user_ids:
            return []
        statement = (
            select(AppUserRow.email, AppUserRow.full_name)
            .where(AppUserRow.id.in_(user_ids), AppUserRow.is_active.is_(True))
            .order_by(AppUserRow.created_at)
        )
        async with self._session_factory() as session:
            rows = (await session.execute(statement)).all()
        return [Contact(email=Email(row.email), full_name=row.full_name) for row in rows]

    async def contacts_by_id(self, user_ids: Collection[UUID]) -> dict[UUID, Contact]:
        """The contact of each of those users, by id, whether or not their account is active:
        a team lists its members even if one of them can no longer sign in (HU-06)."""
        if not user_ids:
            return {}
        statement = select(AppUserRow.id, AppUserRow.email, AppUserRow.full_name).where(
            AppUserRow.id.in_(user_ids)
        )
        async with self._session_factory() as session:
            rows = (await session.execute(statement)).all()
        return {row.id: Contact(email=Email(row.email), full_name=row.full_name) for row in rows}
