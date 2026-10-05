"""The read side of invitations: what the activation page asks (CQRS)."""

from datetime import timedelta

import pytest
from integration_helpers import NOW, make_invitation, make_team, make_user

from agilina_api.identity.domain.invitation import InvitationStatus
from agilina_api.identity.domain.value_objects import TokenHash
from agilina_api.identity.infrastructure.persistence.invitation_queries import SqlInvitationQueries
from agilina_api.identity.infrastructure.persistence.invitation_repository import (
    SqlAlchemyInvitationRepository,
)
from agilina_api.identity.infrastructure.persistence.user_repository import SqlAlchemyUserRepository
from agilina_api.shared.infrastructure.database.unit_of_work import SqlAlchemyUnitOfWork
from agilina_api.teams.infrastructure.persistence.team_repository import SqlAlchemyTeamRepository
from agilina_shared.enums import TeamRole

pytestmark = pytest.mark.integration


async def _stored_invitation(session_factory, **overrides):
    team = make_team()
    invitation, token = make_invitation(team.id, **overrides)
    async with SqlAlchemyUnitOfWork(session_factory) as uow:
        await SqlAlchemyTeamRepository(uow.session).add(team)
        await SqlAlchemyInvitationRepository(uow.session).add(invitation)
        await uow.commit()
    return invitation, token


async def test_a_valid_link_reports_who_it_is_for(session_factory):
    invitation, token = await _stored_invitation(session_factory, role=TeamRole.ADMIN)

    view = await SqlInvitationQueries(session_factory).get_status(token.hash(), NOW)

    assert view is not None
    assert view.email == "julian@example.test" and view.full_name == "Julián Torres"
    assert view.role is TeamRole.ADMIN
    assert view.status is InvitationStatus.PENDING
    assert view.expires_at == invitation.expires_at


async def test_a_used_link_reports_accepted(session_factory):
    invitation, token = await _stored_invitation(session_factory)
    user = make_user()
    async with SqlAlchemyUnitOfWork(session_factory) as uow:
        await SqlAlchemyUserRepository(uow.session).add(user)
        repository = SqlAlchemyInvitationRepository(uow.session)
        stored = await repository.get_by_token_hash(token.hash())
        assert stored is not None
        stored.accept(user_id=user.id, now=NOW)
        await repository.save(stored)
        await uow.commit()

    view = await SqlInvitationQueries(session_factory).get_status(token.hash(), NOW)

    assert view is not None and view.status is InvitationStatus.ACCEPTED


async def test_an_overdue_link_reports_expired_even_though_it_is_stored_as_pending(session_factory):
    invitation, token = await _stored_invitation(session_factory)

    view = await SqlInvitationQueries(session_factory).get_status(
        token.hash(), NOW + timedelta(days=8)
    )

    assert view is not None and view.status is InvitationStatus.EXPIRED


async def test_the_read_side_agrees_with_the_aggregate_at_the_exact_deadline(session_factory):
    invitation, token = await _stored_invitation(session_factory)
    queries = SqlInvitationQueries(session_factory)
    just_before = invitation.expires_at - timedelta(microseconds=1)

    before = await queries.get_status(token.hash(), just_before)
    at_deadline = await queries.get_status(token.hash(), invitation.expires_at)

    assert before is not None and at_deadline is not None
    assert before.status is invitation.state_at(just_before) is InvitationStatus.PENDING
    assert (
        at_deadline.status is invitation.state_at(invitation.expires_at) is InvitationStatus.EXPIRED
    )


async def test_an_altered_link_reports_nothing(session_factory):
    assert await SqlInvitationQueries(session_factory).get_status(TokenHash("f" * 64), NOW) is None
