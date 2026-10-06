"""The members of a team, for its settings screen (HU-06, acceptance criteria 1, 3 and 5)."""

from dataclasses import dataclass
from uuid import UUID

from agilina_api.teams.application.dtos import (
    MemberRecord,
    MemberView,
    RoleOption,
    TeamMembersList,
)
from agilina_api.teams.application.ports.outbound import MemberContactsDirectory, TeamQueries
from agilina_api.teams.domain.member_rules import removal_blocker, role_change_blocker
from agilina_shared.enums import TeamRole


@dataclass(frozen=True)
class ListTeamMembers:
    team_id: UUID


def _label_of(role: TeamRole) -> str:
    # HU-04 replaces this with the visible-label resolver (role + the team's mode); until
    # then the label is the code of the internal role.
    return role.value


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
            MemberView(
                user_id=record.user_id,
                full_name=contacts[record.user_id].full_name,
                email=contacts[record.user_id].email,
                role=record.role,
                label=_label_of(record.role),
                role_change_blocked_by=role_change_blocker(
                    role=record.role,
                    admin_count=admin_count,
                    sprint_in_progress=stored.has_active_sprint,
                ),
                removal_blocked_by=removal_blocker(role=record.role, admin_count=admin_count),
            )
            for record in records
        ]
        members.sort(key=lambda member: (member.full_name.casefold(), member.email))
        return TeamMembersList(
            roles=tuple(RoleOption(role=role, label=_label_of(role)) for role in TeamRole),
            members=tuple(members),
        )
