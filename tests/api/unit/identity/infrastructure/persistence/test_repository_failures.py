"""What the repositories do with a database error that is not the one they translate."""

import pytest
from sqlalchemy.exc import IntegrityError

from agilina_api.identity.domain.errors import (
    PendingInvitationAlreadyExistsError,
    UnknownTeamError,
    UserAlreadyExistsError,
)
from agilina_api.identity.infrastructure.persistence.invitation_repository import (
    PENDING_UNIQUE,
    TEAM_FOREIGN_KEY,
    SqlAlchemyInvitationRepository,
)
from agilina_api.identity.infrastructure.persistence.user_contacts import SqlUserContacts
from agilina_api.identity.infrastructure.persistence.user_repository import (
    SqlAlchemyUserRepository,
)
from tests.api.builders import AppUserBuilder, InvitationBuilder
from tests.api.doubles.database import FailingSession, integrity_error


async def test_a_duplicate_pending_invitation_is_translated():
    repository = SqlAlchemyInvitationRepository(FailingSession(integrity_error(PENDING_UNIQUE)))  # type: ignore[arg-type]

    with pytest.raises(PendingInvitationAlreadyExistsError):
        await repository.add(InvitationBuilder().build())


async def test_a_missing_team_is_translated():
    repository = SqlAlchemyInvitationRepository(FailingSession(integrity_error(TEAM_FOREIGN_KEY)))  # type: ignore[arg-type]

    with pytest.raises(UnknownTeamError):
        await repository.add(InvitationBuilder().build())


async def test_any_other_integrity_error_is_not_hidden_behind_an_invitation_error():
    repository = SqlAlchemyInvitationRepository(FailingSession(integrity_error("something_else")))  # type: ignore[arg-type]

    with pytest.raises(IntegrityError):
        await repository.add(InvitationBuilder().build())


async def test_a_duplicate_email_or_identity_is_translated_for_users():
    repository = SqlAlchemyUserRepository(FailingSession(integrity_error("app_user_email_key")))  # type: ignore[arg-type]

    with pytest.raises(UserAlreadyExistsError):
        await repository.add(AppUserBuilder().build())


async def test_any_other_integrity_error_is_not_hidden_behind_a_user_error():
    repository = SqlAlchemyUserRepository(FailingSession(integrity_error(None)))  # type: ignore[arg-type]

    with pytest.raises(IntegrityError):
        await repository.add(AppUserBuilder().build())


async def test_nobody_to_look_up_means_no_query_at_all():
    contacts = SqlUserContacts(session_factory=None)  # type: ignore[arg-type]

    assert await contacts.get_contacts([]) == []
