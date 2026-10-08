from agilina_api.teams.application.dtos import (
    MemberRecord,
    RoleOption,
    TeamMembersList,
)
from agilina_api.teams.application.ports.outbound import MemberContactsDirectory, TeamQueries
from agilina_api.teams.application.queries.build_member_view import build_member_view
from agilina_api.teams.application.queries.list_team_members.list_team_members import (
    ListTeamMembers,
)
from agilina_shared import role_label
from agilina_shared.enums import TeamRole


def _admin_count(records: tuple[MemberRecord, ...]) -> int:
    return sum(1 for record in records if record.role is TeamRole.ADMIN)


class ListTeamMembersHandler:
    """Joins what teams stores (who and with which role) with what identity knows (name
    and email), and tells for each member why their role cannot change or why they cannot
    be removed, with the same rules the commands enforce, so the interface computes none.
    It does not check who asks: the route lets only the team's admins get here.
    """

    def __init__(self, queries: TeamQueries, contacts: MemberContactsDirectory) -> None:
        self._queries = queries
        self._contacts = contacts

    async def handle(self, query: ListTeamMembers) -> TeamMembersList:
        stored = await self._queries.list_members(query.team_id)
        records = stored.members
        admin_count = _admin_count(records)
        # Every membership points to an existing account (a foreign key), so each one has
        # its contact.
        contacts = await self._contacts.contacts_of([record.user_id for record in records])
        members = [
            build_member_view(
                record,
                contacts[record.user_id],
                admin_count=admin_count,
                has_active_sprint=stored.has_active_sprint,
                mode=stored.mode,
            )
            for record in records
        ]
        members.sort(key=lambda member: (member.full_name.casefold(), member.email))
        return TeamMembersList(
            roles=tuple(
                RoleOption(role=role, label=role_label(role, stored.mode)) for role in TeamRole
            ),
            members=tuple(members),
        )
