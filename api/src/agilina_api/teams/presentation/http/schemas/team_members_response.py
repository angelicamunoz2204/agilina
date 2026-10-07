from pydantic import BaseModel, Field

from agilina_api.teams.presentation.http.schemas.role_option_response import RoleOptionResponse
from agilina_api.teams.presentation.http.schemas.team_member_response import TeamMemberResponse


class TeamMembersResponse(BaseModel):
    roles: list[RoleOptionResponse] = Field(
        description="The roles an admin can give, with their labels, in the order to show them."
    )
    members: list[TeamMemberResponse] = Field(
        description="The team's active members, ordered by name ignoring case."
    )
