"""The user repository against a real PostgreSQL."""

import pytest
from integration_helpers import make_user

from agilina_api.identity.domain.errors import UserAlreadyExistsError
from agilina_api.identity.domain.value_objects import Email
from agilina_api.identity.infrastructure.persistence.user_repository import SqlAlchemyUserRepository
from agilina_api.shared.infrastructure.database.unit_of_work import SqlAlchemyUnitOfWork

pytestmark = pytest.mark.integration


async def test_a_user_can_be_found_by_email_in_any_case_and_by_keycloak_subject(session_factory):
    user = make_user(email=Email("julian@example.test"), keycloak_subject="kc-123")
    async with SqlAlchemyUnitOfWork(session_factory) as uow:
        await SqlAlchemyUserRepository(uow.session).add(user)
        await uow.commit()

    async with SqlAlchemyUnitOfWork(session_factory) as uow:
        repository = SqlAlchemyUserRepository(uow.session)
        by_email = await repository.get_by_email(Email("JULIAN@Example.test"))
        by_subject = await repository.get_by_keycloak_subject("kc-123")

    assert by_email is not None and by_email.id == user.id
    assert by_subject is not None and by_subject.email == user.email
    assert by_subject.full_name == "Julián Torres" and by_subject.is_active is True


async def test_unknown_users_are_not_found(session_factory):
    async with SqlAlchemyUnitOfWork(session_factory) as uow:
        repository = SqlAlchemyUserRepository(uow.session)
        assert await repository.get_by_email(Email("nobody@example.test")) is None
        assert await repository.get_by_keycloak_subject("nope") is None


async def test_the_same_email_cannot_register_twice_whatever_its_case(session_factory):
    async with SqlAlchemyUnitOfWork(session_factory) as uow:
        repository = SqlAlchemyUserRepository(uow.session)
        await repository.add(make_user(email=Email("julian@example.test")))
        with pytest.raises(UserAlreadyExistsError):
            await repository.add(make_user(email=Email("JULIAN@example.test")))


async def test_the_same_keycloak_identity_cannot_be_linked_twice(session_factory):
    async with SqlAlchemyUnitOfWork(session_factory) as uow:
        repository = SqlAlchemyUserRepository(uow.session)
        await repository.add(make_user(keycloak_subject="kc-1"))
        with pytest.raises(UserAlreadyExistsError):
            await repository.add(make_user(keycloak_subject="kc-1"))
