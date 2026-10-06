"""Adapters that connect one bounded context to another.

``identity`` and ``teams`` cannot import each other (AD-21), so each declares what it needs
from the other as ports; the implementations live here, in the composition root, which is
the only place allowed to know both.
"""

from collections.abc import Callable, Collection
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from agilina_api.identity.application.dtos import TeamContacts
from agilina_api.identity.application.ports.outbound import TeamContactsDirectory, TeamMembership
from agilina_api.identity.domain.errors import AlreadyTeamMemberError, UnknownTeamError
from agilina_api.identity.infrastructure.persistence.user_contacts import SqlUserContacts
from agilina_api.shared.application.ports import Clock
from agilina_api.teams.application.commands.add_member import AddTeamMember, AddTeamMemberHandler
from agilina_api.teams.application.dtos import MemberContact
from agilina_api.teams.application.ports.outbound import MemberContactsDirectory, TeamQueries
from agilina_api.teams.domain.errors import AlreadyMemberError, TeamNotFoundError
from agilina_api.teams.infrastructure.persistence.team_repository import SqlAlchemyTeamRepository
from agilina_shared.enums import TeamRole


class TeamsBackedMembership(TeamMembership):
    """Adding a member, through the teams use case, inside the identity transaction."""

    def __init__(self, session: AsyncSession, clock: Clock) -> None:
        self._handler = AddTeamMemberHandler(SqlAlchemyTeamRepository(session), clock)

    async def add_member(self, *, team_id: UUID, user_id: UUID, role: TeamRole) -> None:
        try:
            await self._handler.handle(AddTeamMember(team_id=team_id, user_id=user_id, role=role))
        except TeamNotFoundError as error:
            raise UnknownTeamError(str(error)) from error
        except AlreadyMemberError as error:
            raise AlreadyTeamMemberError(str(error)) from error


def team_membership_factory(clock: Clock) -> Callable[[AsyncSession], TeamMembership]:
    return lambda session: TeamsBackedMembership(session, clock)


class TeamsBackedContacts(TeamContactsDirectory):
    """A team's name, language and admins: the first from teams, the e-mails from identity."""

    def __init__(self, team_queries: TeamQueries, user_contacts: SqlUserContacts) -> None:
        self._team_queries = team_queries
        self._user_contacts = user_contacts

    async def get(self, team_id: UUID) -> TeamContacts | None:
        summary = await self._team_queries.get_summary(team_id)
        if summary is None:
            return None
        admins = await self._user_contacts.get_contacts(summary.admin_user_ids)
        return TeamContacts(team_name=summary.name, language=summary.language, admins=tuple(admins))


class IdentityBackedMemberContacts(MemberContactsDirectory):
    """The names and emails of a team's members, for teams, from identity's accounts."""

    def __init__(self, user_contacts: SqlUserContacts) -> None:
        self._user_contacts = user_contacts

    async def contacts_of(self, user_ids: Collection[UUID]) -> dict[UUID, MemberContact]:
        contacts = await self._user_contacts.contacts_by_id(user_ids)
        return {
            user_id: MemberContact(full_name=contact.full_name, email=contact.email.value)
            for user_id, contact in contacts.items()
        }
