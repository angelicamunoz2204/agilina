from collections.abc import Collection
from uuid import UUID

from agilina_api.identity.infrastructure.persistence.user_contacts import SqlUserContacts
from agilina_api.teams.application.dtos import MemberContact
from agilina_api.teams.application.ports.outbound import MemberContactsDirectory


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
