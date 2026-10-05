"""The team repository against a real PostgreSQL."""

from datetime import timedelta
from uuid import uuid4

import pytest
from integration_helpers import NOW, make_team, make_user
from sqlalchemy import text

from agilina_api.identity.infrastructure.persistence.user_repository import SqlAlchemyUserRepository
from agilina_api.shared.infrastructure.database.unit_of_work import SqlAlchemyUnitOfWork
from agilina_api.teams.domain.team import MembershipStatus
from agilina_api.teams.infrastructure.persistence.team_repository import SqlAlchemyTeamRepository
from agilina_shared.enums import Language, OperationMode, TeamRole

pytestmark = pytest.mark.integration


async def _stored_user(session_factory):
    user = make_user()
    async with SqlAlchemyUnitOfWork(session_factory) as uow:
        await SqlAlchemyUserRepository(uow.session).add(user)
        await uow.commit()
    return user


async def test_a_team_created_by_the_operator_round_trips_without_an_author(session_factory):
    team = make_team(
        name="Atlas", created_by=None, language=Language.ES, mode=OperationMode.AUTONOMOUS
    )
    async with SqlAlchemyUnitOfWork(session_factory) as uow:
        await SqlAlchemyTeamRepository(uow.session).add(team)
        await uow.commit()

    async with SqlAlchemyUnitOfWork(session_factory) as uow:
        loaded = await SqlAlchemyTeamRepository(uow.session).get(team.id)

    assert loaded is not None
    assert (loaded.name, loaded.created_by) == ("Atlas", None)
    assert loaded.language is Language.ES and loaded.mode is OperationMode.AUTONOMOUS
    assert loaded.memberships == ()


async def test_an_unknown_team_is_not_found(session_factory):
    async with SqlAlchemyUnitOfWork(session_factory) as uow:
        assert await SqlAlchemyTeamRepository(uow.session).get(uuid4()) is None


async def test_a_new_member_is_stored_with_the_team(session_factory):
    user = await _stored_user(session_factory)
    team = make_team()
    team.add_member(membership_id=uuid4(), user_id=user.id, role=TeamRole.ADMIN, now=NOW)
    async with SqlAlchemyUnitOfWork(session_factory) as uow:
        await SqlAlchemyTeamRepository(uow.session).add(team)
        await uow.commit()

    async with SqlAlchemyUnitOfWork(session_factory) as uow:
        loaded = await SqlAlchemyTeamRepository(uow.session).get(team.id)

    assert loaded is not None
    membership = loaded.membership_of(user.id)
    assert membership is not None and membership.role is TeamRole.ADMIN
    assert membership.status is MembershipStatus.ACTIVE and membership.joined_at == NOW
    assert loaded.admin_count == 1


async def test_a_member_added_later_is_saved_and_the_team_keeps_the_rest(session_factory):
    first, second = await _stored_user(session_factory), await _stored_user(session_factory)
    team = make_team()
    team.add_member(membership_id=uuid4(), user_id=first.id, role=TeamRole.ADMIN, now=NOW)
    async with SqlAlchemyUnitOfWork(session_factory) as uow:
        await SqlAlchemyTeamRepository(uow.session).add(team)
        await uow.commit()

    async with SqlAlchemyUnitOfWork(session_factory) as uow:
        repository = SqlAlchemyTeamRepository(uow.session)
        loaded = await repository.get(team.id)
        assert loaded is not None
        loaded.add_member(
            membership_id=uuid4(),
            user_id=second.id,
            role=TeamRole.MEMBER,
            now=NOW + timedelta(days=1),
        )
        await repository.save(loaded)
        await uow.commit()

    async with SqlAlchemyUnitOfWork(session_factory) as uow:
        after = await SqlAlchemyTeamRepository(uow.session).get(team.id)

    assert after is not None and len(after.memberships) == 2
    assert {m.user_id for m in after.memberships} == {first.id, second.id}


async def test_saving_leaves_the_columns_the_domain_does_not_know_untouched(
    session_factory, engine
):
    """slack_user_id belongs to a later story: a save must not erase it."""
    user = await _stored_user(session_factory)
    team = make_team()
    team.add_member(membership_id=uuid4(), user_id=user.id, role=TeamRole.MEMBER, now=NOW)
    async with SqlAlchemyUnitOfWork(session_factory) as uow:
        await SqlAlchemyTeamRepository(uow.session).add(team)
        await uow.commit()
    async with engine.begin() as connection:
        await connection.execute(text("UPDATE team_member SET slack_user_id = 'U123'"))

    async with SqlAlchemyUnitOfWork(session_factory) as uow:
        repository = SqlAlchemyTeamRepository(uow.session)
        loaded = await repository.get(team.id)
        assert loaded is not None
        await repository.save(loaded)
        await uow.commit()

    async with engine.connect() as connection:
        assert (
            await connection.execute(text("SELECT slack_user_id FROM team_member"))
        ).scalar_one() == "U123"
