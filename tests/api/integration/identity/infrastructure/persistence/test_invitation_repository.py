"""The invitation repository against a real PostgreSQL."""

import asyncio
from datetime import timedelta

import pytest

from agilina_api.identity.domain.errors import (
    InvitationAlreadyUsedError,
    PendingInvitationAlreadyExistsError,
    UnknownTeamError,
)
from agilina_api.identity.domain.invitation import InvitationStatus
from agilina_api.identity.domain.value_objects import Email, TokenHash
from agilina_api.identity.infrastructure.persistence.invitation_repository import (
    SqlAlchemyInvitationRepository,
)
from agilina_api.shared.infrastructure.database.unit_of_work import SqlAlchemyUnitOfWork
from agilina_shared.enums import TeamRole
from tests.api.builders import NOW, InvitationBuilder, TeamBuilder, next_id
from tests.api.integration.support import stored_team, stored_user

pytestmark = pytest.mark.integration


async def test_an_invitation_survives_a_round_trip_with_all_its_data(session_factory):
    team = await stored_team(session_factory)
    builder = (
        InvitationBuilder()
        .for_team(team.id)
        .with_unique_token()
        .with_email("Julian@Example.test")
        .as_admin()
    )
    invitation, token = builder.build(), builder.activation_token

    async with SqlAlchemyUnitOfWork(session_factory) as uow:
        await SqlAlchemyInvitationRepository(uow.session).add(invitation)
        await uow.commit()

    async with SqlAlchemyUnitOfWork(session_factory) as uow:
        loaded = await SqlAlchemyInvitationRepository(uow.session).get_by_token_hash(token.hash())

    assert loaded is not None
    assert loaded.id == invitation.id and loaded.team_id == team.id
    assert loaded.email == Email("julian@example.test")  # stored lowercased
    assert loaded.full_name == "Julián Torres"
    assert loaded.role is TeamRole.ADMIN
    assert loaded.status is InvitationStatus.PENDING
    assert loaded.expires_at == NOW + timedelta(days=7)
    assert loaded.created_by is None and loaded.accepted_at is None


async def test_only_the_hash_is_stored_never_the_token(session_factory, engine):
    team = await stored_team(session_factory)
    builder = InvitationBuilder().for_team(team.id).with_unique_token()
    invitation, token = builder.build(), builder.activation_token
    async with SqlAlchemyUnitOfWork(session_factory) as uow:
        await SqlAlchemyInvitationRepository(uow.session).add(invitation)
        await uow.commit()

    from sqlalchemy import text

    async with engine.connect() as connection:
        stored = (await connection.execute(text("SELECT token_hash FROM invitation"))).scalar_one()

    assert stored == token.hash().value
    assert token.value not in stored


async def test_an_unknown_or_altered_token_finds_nothing(session_factory):
    async with SqlAlchemyUnitOfWork(session_factory) as uow:
        repository = SqlAlchemyInvitationRepository(uow.session)
        assert await repository.get_by_token_hash(TokenHash("0" * 64)) is None


async def test_a_second_pending_invitation_for_the_same_email_in_a_team_is_refused(session_factory):
    team = await stored_team(session_factory)
    first = (
        InvitationBuilder()
        .for_team(team.id)
        .with_unique_token()
        .with_email("julian@example.test")
        .build()
    )
    # CITEXT: the same email, whatever its case
    again = (
        InvitationBuilder()
        .for_team(team.id)
        .with_unique_token()
        .with_email("JULIAN@example.test")
        .build()
    )

    async with SqlAlchemyUnitOfWork(session_factory) as uow:
        repository = SqlAlchemyInvitationRepository(uow.session)
        await repository.add(first)
        with pytest.raises(PendingInvitationAlreadyExistsError):
            await repository.add(again)


async def test_the_same_email_can_be_invited_to_another_team(session_factory):
    atlas, borealis = (
        await stored_team(session_factory, TeamBuilder().named("Atlas")),
        await stored_team(session_factory, TeamBuilder().named("Borealis")),
    )

    async with SqlAlchemyUnitOfWork(session_factory) as work:
        repository = SqlAlchemyInvitationRepository(work.session)
        await repository.add(
            InvitationBuilder()
            .for_team(atlas.id)
            .with_unique_token()
            .with_email("julian@example.test")
            .build()
        )
        await repository.add(
            InvitationBuilder()
            .for_team(borealis.id)
            .with_unique_token()
            .with_email("julian@example.test")
            .build()
        )
        await work.commit()


async def test_a_new_invitation_is_allowed_once_the_previous_one_was_used(session_factory):
    team = await stored_team(session_factory)
    builder = InvitationBuilder().for_team(team.id).with_unique_token()
    first = builder.build()
    user = await stored_user(session_factory)
    async with SqlAlchemyUnitOfWork(session_factory) as uow:
        repository = SqlAlchemyInvitationRepository(uow.session)
        await repository.add(first)
        first.accept(user_id=user.id, now=NOW)
        await repository.save(first)
        await repository.add(
            InvitationBuilder().for_team(team.id).with_unique_token().build()
        )  # the index only covers pending ones
        await uow.commit()


async def test_an_overdue_invitation_must_have_its_expiry_stored_before_inviting_again(
    session_factory,
):
    """The stored status stays 'pending' after the deadline; the index would refuse a new one."""
    team = await stored_team(session_factory)
    old = InvitationBuilder().for_team(team.id).with_unique_token().build()
    later = NOW + timedelta(days=8)
    async with SqlAlchemyUnitOfWork(session_factory) as uow:
        repository = SqlAlchemyInvitationRepository(uow.session)
        await repository.add(old)
        await uow.commit()

    async with SqlAlchemyUnitOfWork(session_factory) as uow:
        repository = SqlAlchemyInvitationRepository(uow.session)
        stale = await repository.find_pending(team.id, Email("julian@example.test"))
        assert stale is not None and stale.state_at(later) is InvitationStatus.EXPIRED
        assert stale.expire_if_due(later) is True
        await repository.save(stale)
        await repository.add(InvitationBuilder().for_team(team.id).with_unique_token().build())
        await uow.commit()


async def test_saving_stores_the_acceptance_and_nothing_else_changes(session_factory):
    team = await stored_team(session_factory)
    builder = InvitationBuilder().for_team(team.id).with_unique_token()
    invitation, token = builder.build(), builder.activation_token
    user_id = (await stored_user(session_factory)).id
    async with SqlAlchemyUnitOfWork(session_factory) as uow:
        repository = SqlAlchemyInvitationRepository(uow.session)
        await repository.add(invitation)
        await uow.commit()
    async with SqlAlchemyUnitOfWork(session_factory) as uow:
        repository = SqlAlchemyInvitationRepository(uow.session)
        loaded = await repository.get_by_token_hash(token.hash())
        assert loaded is not None
        loaded.accept(user_id=user_id, now=NOW + timedelta(days=1))
        await repository.save(loaded)
        await uow.commit()

    async with SqlAlchemyUnitOfWork(session_factory) as uow:
        after = await SqlAlchemyInvitationRepository(uow.session).get_by_token_hash(token.hash())

    assert after is not None
    assert after.status is InvitationStatus.ACCEPTED
    assert after.accepted_at == NOW + timedelta(days=1)
    assert after.accepted_user_id == user_id
    assert after.email == invitation.email and after.expires_at == invitation.expires_at


async def test_find_pending_never_returns_another_teams_invitation(session_factory):
    atlas, borealis = (
        await stored_team(session_factory, TeamBuilder().named("Atlas")),
        await stored_team(session_factory, TeamBuilder().named("Borealis")),
    )
    async with SqlAlchemyUnitOfWork(session_factory) as work:
        repository = SqlAlchemyInvitationRepository(work.session)
        await repository.add(
            InvitationBuilder()
            .for_team(atlas.id)
            .with_unique_token()
            .with_email("julian@example.test")
            .build()
        )
        await work.commit()

    async with SqlAlchemyUnitOfWork(session_factory) as work:
        repository = SqlAlchemyInvitationRepository(work.session)
        assert await repository.find_pending(atlas.id, Email("JULIAN@example.test")) is not None
        assert await repository.find_pending(borealis.id, Email("julian@example.test")) is None


async def test_an_invitation_for_a_team_that_does_not_exist_is_refused_by_the_database(
    session_factory,
):
    invitation = InvitationBuilder().for_team(next_id()).with_unique_token().build()

    async with SqlAlchemyUnitOfWork(session_factory) as uow:
        with pytest.raises(UnknownTeamError):
            await SqlAlchemyInvitationRepository(uow.session).add(invitation)


async def test_leaving_the_unit_of_work_without_committing_discards_the_changes(session_factory):
    team = await stored_team(session_factory)
    builder = InvitationBuilder().for_team(team.id).with_unique_token()
    invitation, token = builder.build(), builder.activation_token

    async with SqlAlchemyUnitOfWork(session_factory) as uow:
        await SqlAlchemyInvitationRepository(uow.session).add(invitation)  # no commit

    async with SqlAlchemyUnitOfWork(session_factory) as uow:
        assert (
            await SqlAlchemyInvitationRepository(uow.session).get_by_token_hash(token.hash())
            is None
        )


async def test_an_error_inside_the_unit_of_work_discards_the_changes(session_factory):
    team = await stored_team(session_factory)
    builder = InvitationBuilder().for_team(team.id).with_unique_token()
    invitation, token = builder.build(), builder.activation_token

    with pytest.raises(RuntimeError, match="boom"):
        async with SqlAlchemyUnitOfWork(session_factory) as uow:
            await SqlAlchemyInvitationRepository(uow.session).add(invitation)
            raise RuntimeError("boom")

    async with SqlAlchemyUnitOfWork(session_factory) as uow:
        assert (
            await SqlAlchemyInvitationRepository(uow.session).get_by_token_hash(token.hash())
            is None
        )


async def test_two_simultaneous_activations_of_the_same_link_let_only_one_win(session_factory):
    """The row lock taken by get_by_token_hash makes the second one wait, then fail."""
    team = await stored_team(session_factory)
    builder = InvitationBuilder().for_team(team.id).with_unique_token()
    invitation, token = builder.build(), builder.activation_token
    winner, loser = await stored_user(session_factory), await stored_user(session_factory)
    async with SqlAlchemyUnitOfWork(session_factory) as uow:
        await SqlAlchemyInvitationRepository(uow.session).add(invitation)
        await uow.commit()

    first_holds_the_lock = asyncio.Event()
    order: list[str] = []

    async def activate(
        user_id, label: str, wait_for: asyncio.Event | None, announce: asyncio.Event | None
    ):
        async with SqlAlchemyUnitOfWork(session_factory) as uow:
            repository = SqlAlchemyInvitationRepository(uow.session)
            found = await repository.get_by_token_hash(token.hash())
            assert found is not None
            if announce is not None:
                announce.set()  # I hold the lock now
                await asyncio.sleep(0.5)  # long enough for the other one to try and block
            if wait_for is not None:
                await wait_for.wait()
            found.accept(user_id=user_id, now=NOW)  # raises if someone already used it
            await repository.save(found)
            await uow.commit()
            order.append(label)

    async def second():
        await first_holds_the_lock.wait()
        await activate(loser.id, "second", None, None)

    results = await asyncio.gather(
        activate(winner.id, "first", None, first_holds_the_lock), second(), return_exceptions=True
    )

    assert order == ["first"]
    assert results[0] is None
    assert isinstance(results[1], InvitationAlreadyUsedError)


async def test_saving_an_invitation_that_was_never_stored_is_an_error(session_factory):
    async with SqlAlchemyUnitOfWork(session_factory) as uow:
        with pytest.raises(LookupError, match="does not exist"):
            await SqlAlchemyInvitationRepository(uow.session).save(InvitationBuilder().build())
