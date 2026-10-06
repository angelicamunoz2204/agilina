"""The team repository against a real PostgreSQL."""

from datetime import timedelta

import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from agilina_api.shared.infrastructure.database.unit_of_work import SqlAlchemyUnitOfWork
from agilina_api.teams.domain.team import MembershipStatus
from agilina_api.teams.infrastructure.persistence.team_repository import SqlAlchemyTeamRepository
from agilina_shared.enums import Language, OperationMode, TeamRole
from tests.api.builders import NOW, TeamBuilder, next_id
from tests.api.integration.support import stored_team, stored_user

pytestmark = pytest.mark.integration


async def test_a_team_created_by_the_operator_round_trips_without_an_author(session_factory):
    team = await stored_team(
        session_factory,
        TeamBuilder().named("Atlas").in_language(Language.ES).in_mode(OperationMode.AUTONOMOUS),
    )

    async with SqlAlchemyUnitOfWork(session_factory) as uow:
        loaded = await SqlAlchemyTeamRepository(uow.session).get(team.id)

    assert loaded is not None
    assert (loaded.name, loaded.created_by) == ("Atlas", None)
    assert loaded.language is Language.ES and loaded.mode is OperationMode.AUTONOMOUS
    assert loaded.memberships == ()


async def test_an_unknown_team_is_not_found(session_factory):
    async with SqlAlchemyUnitOfWork(session_factory) as uow:
        assert await SqlAlchemyTeamRepository(uow.session).get(next_id()) is None


async def test_a_new_member_is_stored_with_the_team(session_factory):
    user = await stored_user(session_factory)
    team = await stored_team(session_factory, TeamBuilder().with_admin(user.id))

    async with SqlAlchemyUnitOfWork(session_factory) as uow:
        loaded = await SqlAlchemyTeamRepository(uow.session).get(team.id)

    assert loaded is not None
    membership = loaded.membership_of(user.id)
    assert membership is not None and membership.role is TeamRole.ADMIN
    assert membership.status is MembershipStatus.ACTIVE and membership.joined_at == NOW
    assert loaded.admin_count == 1


async def test_a_member_added_later_is_saved_and_the_team_keeps_the_rest(session_factory):
    first, second = await stored_user(session_factory), await stored_user(session_factory)
    team = await stored_team(session_factory, TeamBuilder().with_admin(first.id))

    async with SqlAlchemyUnitOfWork(session_factory) as uow:
        repository = SqlAlchemyTeamRepository(uow.session)
        loaded = await repository.get(team.id)
        assert loaded is not None
        loaded.add_member(
            membership_id=next_id(),
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
    user = await stored_user(session_factory)
    team = await stored_team(session_factory, TeamBuilder().with_member(user.id))
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


async def test_saving_a_team_that_was_never_stored_is_an_error(session_factory):
    async with SqlAlchemyUnitOfWork(session_factory) as uow:
        with pytest.raises(LookupError, match="does not exist"):
            await SqlAlchemyTeamRepository(uow.session).save(TeamBuilder().build())


async def test_a_team_created_by_a_user_is_stored_with_its_admin(session_factory):
    user = await stored_user(session_factory)
    team = await stored_team(session_factory, TeamBuilder().created_with_admin(user.id))

    async with SqlAlchemyUnitOfWork(session_factory) as uow:
        loaded = await SqlAlchemyTeamRepository(uow.session).get(team.id)

    assert loaded is not None and loaded.created_by == user.id
    membership = loaded.membership_of(user.id)
    assert membership is not None and membership.role is TeamRole.ADMIN and membership.is_active


async def test_if_a_membership_fails_the_team_is_not_stored(session_factory, engine):
    """The team row is flushed before its members: a member that cannot be stored (a user
    that does not exist breaks the foreign key) must take the team down with it."""
    user = await stored_user(session_factory)
    team = TeamBuilder().created_with_admin(user.id).with_member(next_id()).build()

    async with SqlAlchemyUnitOfWork(session_factory) as uow:
        with pytest.raises(IntegrityError):
            await SqlAlchemyTeamRepository(uow.session).add(team)

    async with engine.connect() as connection:
        assert (await connection.execute(text("SELECT count(*) FROM team"))).scalar_one() == 0
        assert (
            await connection.execute(text("SELECT count(*) FROM team_member"))
        ).scalar_one() == 0
