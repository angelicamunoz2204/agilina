"""The user repository against a real PostgreSQL."""

import pytest

from agilina_api.identity.domain.errors import UserAlreadyExistsError
from agilina_api.identity.domain.value_objects import Email
from agilina_api.identity.infrastructure.persistence.user_repository import SqlAlchemyUserRepository
from agilina_api.shared.infrastructure.database.unit_of_work import SqlAlchemyUnitOfWork
from tests.api.builders import AppUserBuilder, next_id
from tests.api.integration.support import stored_user

pytestmark = pytest.mark.integration


async def test_a_user_can_be_found_by_email_in_any_case_and_by_keycloak_subject(session_factory):
    user = await stored_user(
        session_factory, AppUserBuilder().with_email("julian@example.test").with_subject("kc-123")
    )

    async with SqlAlchemyUnitOfWork(session_factory) as uow:
        repository = SqlAlchemyUserRepository(uow.session)
        by_email = await repository.get_by_email(Email("JULIAN@Example.test"))
        by_subject = await repository.get_by_keycloak_subject("kc-123")

    assert by_email is not None and by_email.id == user.id
    assert by_subject is not None and by_subject.email == user.email
    assert by_subject.full_name == "Julián Torres" and by_subject.is_active is True


async def test_a_user_can_be_found_by_id_also_when_disabled(session_factory):
    active = await stored_user(session_factory, AppUserBuilder().with_unique_email().named("Ana"))
    disabled = await stored_user(session_factory, AppUserBuilder().with_unique_email().disabled())

    async with SqlAlchemyUnitOfWork(session_factory) as uow:
        repository = SqlAlchemyUserRepository(uow.session)
        found = await repository.get(active.id)
        found_disabled = await repository.get(disabled.id)

    assert found is not None and (found.id, found.full_name) == (active.id, "Ana")
    assert found.email == active.email and found.is_active is True
    assert found_disabled is not None and found_disabled.is_active is False


async def test_unknown_users_are_not_found(session_factory):
    async with SqlAlchemyUnitOfWork(session_factory) as uow:
        repository = SqlAlchemyUserRepository(uow.session)
        assert await repository.get(next_id()) is None
        assert await repository.get_by_email(Email("nobody@example.test")) is None
        assert await repository.get_by_keycloak_subject("nope") is None


async def test_the_same_email_cannot_register_twice_whatever_its_case(session_factory):
    async with SqlAlchemyUnitOfWork(session_factory) as uow:
        repository = SqlAlchemyUserRepository(uow.session)
        await repository.add(AppUserBuilder().with_email("julian@example.test").build())
        with pytest.raises(UserAlreadyExistsError):
            await repository.add(AppUserBuilder().with_email("JULIAN@example.test").build())


async def test_the_same_keycloak_identity_cannot_be_linked_twice(session_factory):
    async with SqlAlchemyUnitOfWork(session_factory) as uow:
        repository = SqlAlchemyUserRepository(uow.session)
        await repository.add(AppUserBuilder().with_unique_email().with_subject("kc-1").build())
        with pytest.raises(UserAlreadyExistsError):
            await repository.add(AppUserBuilder().with_unique_email().with_subject("kc-1").build())
