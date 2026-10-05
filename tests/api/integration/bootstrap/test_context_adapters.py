"""The adapters that let identity use teams (and vice versa) without knowing each other."""

import pytest

from agilina_api.bootstrap.context_adapters import TeamsBackedContacts, TeamsBackedMembership
from agilina_api.identity.domain.errors import UnknownTeamError
from agilina_api.identity.infrastructure.persistence.user_contacts import SqlUserContacts
from agilina_api.shared.infrastructure.database.unit_of_work import SqlAlchemyUnitOfWork
from agilina_api.teams.infrastructure.persistence.team_queries import SqlTeamQueries
from agilina_shared.enums import Language, TeamRole
from tests.api.builders import AppUserBuilder, TeamBuilder, next_id
from tests.api.doubles import FakeClock
from tests.api.integration.support import stored_team, stored_user

pytestmark = pytest.mark.integration


async def test_a_member_added_to_a_team_that_does_not_exist_is_an_identity_error(session_factory):
    async with SqlAlchemyUnitOfWork(session_factory) as uow:
        membership = TeamsBackedMembership(uow.session, FakeClock())

        with pytest.raises(UnknownTeamError):
            await membership.add_member(team_id=next_id(), user_id=next_id(), role=TeamRole.ADMIN)


def _contacts(session_factory) -> TeamsBackedContacts:
    return TeamsBackedContacts(SqlTeamQueries(session_factory), SqlUserContacts(session_factory))


async def test_the_contacts_of_a_team_are_its_name_its_language_and_its_admins(session_factory):
    admin = await stored_user(
        session_factory, AppUserBuilder().with_unique_email().named("Diego Rojas")
    )
    team = await stored_team(
        session_factory, TeamBuilder().in_language(Language.ES).with_admin(admin.id)
    )

    contacts = await _contacts(session_factory).get(team.id)

    assert contacts is not None
    assert (contacts.team_name, contacts.language) == ("Atlas", Language.ES)
    assert [(c.email, c.full_name) for c in contacts.admins] == [(admin.email, "Diego Rojas")]


async def test_a_team_that_does_not_exist_has_no_contacts(session_factory):
    assert await _contacts(session_factory).get(next_id()) is None
