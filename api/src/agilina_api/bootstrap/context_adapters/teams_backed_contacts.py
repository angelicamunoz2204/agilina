from uuid import UUID

from agilina_api.identity.application.dtos import TeamContacts
from agilina_api.identity.application.ports.outbound import TeamContactsDirectory
from agilina_api.identity.infrastructure.persistence.user_contacts import SqlUserContacts
from agilina_api.teams.application.ports.outbound import TeamQueries


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
