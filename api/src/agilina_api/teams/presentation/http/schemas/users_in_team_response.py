from pydantic import BaseModel, Field

from agilina_api.teams.presentation.http.schemas.role_option_response import RoleOptionResponse
from agilina_api.teams.presentation.http.schemas.user_in_team_response import UserInTeamResponse


class UsersInTeamResponse(BaseModel):
    roles: list[RoleOptionResponse] = Field(
        description="The roles an admin can give, with their labels, in the order to show them."
    )
    users: list[UserInTeamResponse] = Field(
        description="The team's active users, ordered by name ignoring case."
    )
