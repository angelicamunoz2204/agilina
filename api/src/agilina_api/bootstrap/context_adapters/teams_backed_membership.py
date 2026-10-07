from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from agilina_api.identity.application.ports.outbound import TeamMembership
from agilina_api.identity.domain.errors import UnknownTeamError
from agilina_api.shared.application.ports import Clock
from agilina_api.teams.application.commands.add_member import AddTeamMember, AddTeamMemberHandler
from agilina_api.teams.domain.errors import TeamNotFoundError
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
