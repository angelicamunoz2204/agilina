"""The team repository against a real PostgreSQL, including the lock that keeps two
simultaneous changes from leaving a team without an admin (HU-06)."""

import asyncio
import contextlib
from datetime import timedelta
from typing import Self
from uuid import UUID

import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from agilina_api.shared.infrastructure.database.unit_of_work import SqlAlchemyUnitOfWork
from agilina_api.teams.application.commands.change_member_role import ChangeMemberRoleHandler
from agilina_api.teams.domain.errors import LastAdminError
from agilina_api.teams.domain.team import MembershipStatus, Team
from agilina_api.teams.infrastructure.persistence.team_queries import SqlTeamQueries
from agilina_api.teams.infrastructure.persistence.team_repository import SqlAlchemyTeamRepository
from agilina_api.teams.infrastructure.persistence.unit_of_work import SqlAlchemyTeamsUnitOfWork
from agilina_shared.enums import Language, OperationMode, TeamRole
from tests.api.builders import NOW, ChangeMemberRoleBuilder, TeamBuilder, next_id
from tests.api.doubles import FakeClock
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


# ------------------------------------------------- role changes and removals (HU-06) --
async def _changed(session_factory, team_id, change) -> Team:
    """Load the team, apply ``change`` to it, save and commit; then read it back."""
    async with SqlAlchemyUnitOfWork(session_factory) as uow:
        repository = SqlAlchemyTeamRepository(uow.session)
        loaded = await repository.get(team_id)
        assert loaded is not None
        change(loaded)
        await repository.save(loaded)
        await uow.commit()
    async with SqlAlchemyUnitOfWork(session_factory) as uow:
        after = await SqlAlchemyTeamRepository(uow.session).get(team_id)
    assert after is not None
    return after


async def test_a_changed_role_is_saved(session_factory):
    ana, bruno = await stored_user(session_factory), await stored_user(session_factory)
    team = await stored_team(
        session_factory, TeamBuilder().with_admin(ana.id).with_member(bruno.id)
    )

    after = await _changed(
        session_factory,
        team.id,
        lambda t: t.change_member_role(user_id=bruno.id, role=TeamRole.ADMIN, now=NOW),
    )

    membership = after.membership_of(bruno.id)
    assert membership is not None and membership.role is TeamRole.ADMIN
    assert after.admin_count == 2


async def test_a_removal_keeps_the_row_as_removed_with_its_date(session_factory, engine):
    ana, bruno = await stored_user(session_factory), await stored_user(session_factory)
    team = await stored_team(
        session_factory, TeamBuilder().with_admin(ana.id).with_member(bruno.id)
    )
    later = NOW + timedelta(days=2)

    after = await _changed(
        session_factory, team.id, lambda t: t.remove_member(user_id=bruno.id, now=later)
    )

    membership = after.membership_of(bruno.id)
    assert membership is not None and membership.status is MembershipStatus.REMOVED
    assert membership.removed_at == later
    async with engine.connect() as connection:
        users = (await connection.execute(text("SELECT count(*) FROM app_user"))).scalar_one()
    assert users == 2  # the account is identity's: a removal never touches it


async def test_someone_removed_comes_back_through_the_same_row(session_factory):
    ana, bruno = await stored_user(session_factory), await stored_user(session_factory)
    team = await stored_team(
        session_factory, TeamBuilder().with_admin(ana.id).with_removed_member(bruno.id)
    )
    removed = team.membership_of(bruno.id)
    assert removed is not None
    later = NOW + timedelta(days=2)

    after = await _changed(
        session_factory,
        team.id,
        lambda t: t.add_member(
            membership_id=next_id(), user_id=bruno.id, role=TeamRole.ADMIN, now=later
        ),
    )

    back = after.membership_of(bruno.id)
    assert back is not None and back.id == removed.id
    assert back.is_active and back.removed_at is None and back.joined_at == later


class _Rendezvous:
    """Holds whoever arrives until everyone has, or until ``patience`` runs out."""

    def __init__(self, parties: int, patience: float = 1.0) -> None:
        self._parties, self._patience = parties, patience
        self._arrived = 0
        self._everyone = asyncio.Event()

    async def meet(self) -> None:
        self._arrived += 1
        if self._arrived >= self._parties:
            self._everyone.set()
        with contextlib.suppress(TimeoutError):
            await asyncio.wait_for(self._everyone.wait(), self._patience)


class _LoadsThenWaits:
    """The real repository, but after loading a team it waits for the other command to load
    it too: both read before either writes, the worst interleaving. With the row lock the
    second load blocks until the first commits, so the wait runs out instead."""

    def __init__(self, inner: SqlAlchemyTeamRepository, rendezvous: _Rendezvous) -> None:
        self._inner, self._rendezvous = inner, rendezvous

    async def get(self, team_id: UUID) -> Team | None:
        team = await self._inner.get(team_id)
        await self._rendezvous.meet()
        return team

    async def save(self, team: Team) -> None:
        await self._inner.save(team)


class _RacingTeamsUnitOfWork(SqlAlchemyTeamsUnitOfWork):
    def __init__(self, session_factory, rendezvous: _Rendezvous) -> None:
        super().__init__(session_factory)
        self._rendezvous = rendezvous

    async def __aenter__(self) -> Self:
        await super().__aenter__()
        self.teams = _LoadsThenWaits(self.teams, self._rendezvous)
        return self


async def test_two_admins_demoting_each_other_at_once_leave_the_team_one_admin(session_factory):
    """Without the lock each command would see the other still admin and both would pass,
    leaving the team without one. With it the second waits, then sees a single admin."""
    ana, bruno = await stored_user(session_factory), await stored_user(session_factory)
    team = await stored_team(session_factory, TeamBuilder().with_admin(ana.id).with_admin(bruno.id))
    rendezvous = _Rendezvous(parties=2)
    handler = ChangeMemberRoleHandler(
        lambda: _RacingTeamsUnitOfWork(session_factory, rendezvous), FakeClock()
    )
    demote = ChangeMemberRoleBuilder().for_team(team.id).to_role(TeamRole.MEMBER)

    results = await asyncio.gather(
        handler.handle(demote.of_user(ana.id).build()),
        handler.handle(demote.of_user(bruno.id).build()),
        return_exceptions=True,
    )

    assert sorted(type(result).__name__ for result in results) == ["LastAdminError", "NoneType"]
    assert any(isinstance(result, LastAdminError) for result in results)
    listed = await SqlTeamQueries(session_factory).list_members(team.id)
    assert [member.role for member in listed.members].count(TeamRole.ADMIN) == 1
