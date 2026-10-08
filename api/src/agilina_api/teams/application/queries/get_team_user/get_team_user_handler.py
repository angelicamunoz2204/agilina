from agilina_api.teams.application.dtos import MemberView
from agilina_api.teams.application.ports.outbound import MemberContactsDirectory, TeamQueries
from agilina_api.teams.application.queries.build_member_view import build_member_view
from agilina_api.teams.application.queries.get_team_user.get_team_user import GetTeamUser
from agilina_api.teams.domain.errors import MemberNotFoundError
from agilina_shared.enums import TeamRole


class GetTeamUserHandler:
    """One active member of a team with their name, email, role and label in it.

    It does not check who asks: the route decides, an admin for any member and a member for
    themselves (``/v1/users/me``).
    """

    def __init__(self, queries: TeamQueries, contacts: MemberContactsDirectory) -> None:
        self._queries = queries
        self._contacts = contacts

    async def handle(self, query: GetTeamUser) -> MemberView:
        stored = await self._queries.list_members(query.team_id)
        record = next((m for m in stored.members if m.user_id == query.user_id), None)
        if record is None:
            raise MemberNotFoundError(
                f"User {query.user_id} is not an active member of team {query.team_id}"
            )
        contact = (await self._contacts.contacts_of([record.user_id]))[record.user_id]
        admin_count = sum(1 for m in stored.members if m.role is TeamRole.ADMIN)
        return build_member_view(
            record,
            contact,
            admin_count=admin_count,
            has_active_sprint=stored.has_active_sprint,
            mode=stored.mode,
        )
