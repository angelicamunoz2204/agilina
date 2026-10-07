"""Teams API: create a team, list the authenticated user's teams and read one (HU-05), and
manage the team's members (HU-06).

Every route needs an authenticated user, and that user is always the one behind the
access token (``current_user_id``), never one named in the body. A route about one team
is also kept to its members (``current_team_member``), and one that manages its members to
its admins (``current_team_admin``).
"""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Path, Response, status

from agilina_api.shared.application.access import TeamContext
from agilina_api.shared.presentation.http.access import (
    current_team_admin,
    current_team_member,
    current_user_id,
)
from agilina_api.shared.presentation.http.api_error import SharedErrors
from agilina_api.shared.presentation.http.error_schema import errors_of
from agilina_api.teams.application.commands.change_member_role import (
    ChangeMemberRole,
    ChangeMemberRoleHandler,
)
from agilina_api.teams.application.commands.create_team_as_admin import (
    CreateTeamAsAdmin,
    CreateTeamAsAdminHandler,
)
from agilina_api.teams.application.commands.remove_member import RemoveMember, RemoveMemberHandler
from agilina_api.teams.application.queries.get_team import GetTeam, GetTeamHandler
from agilina_api.teams.application.queries.list_my_teams import ListMyTeams, ListMyTeamsHandler
from agilina_api.teams.application.queries.list_team_members import (
    ListTeamMembers,
    ListTeamMembersHandler,
)
from agilina_api.teams.presentation.http.dependencies import (
    get_change_member_role_handler,
    get_create_team_as_admin_handler,
    get_get_team_handler,
    get_list_my_teams_handler,
    get_list_team_members_handler,
    get_remove_member_handler,
)
from agilina_api.teams.presentation.http.errors import TeamsErrors
from agilina_api.teams.presentation.http.presenters import (
    present_created,
    present_members,
    present_my_team,
    present_team,
)
from agilina_api.teams.presentation.http.schemas import (
    ChangeMemberRoleRequest,
    CreatedTeamResponse,
    CreateTeamRequest,
    MyTeamResponse,
    TeamMembersResponse,
    TeamResponse,
)
from agilina_shared.enums import Language, OperationMode, TeamRole

router = APIRouter(prefix="/v1/teams", tags=["teams"])

SIGNED_IN = (
    SharedErrors.TENANT_REQUIRED,
    SharedErrors.TENANT_NOT_FOUND,
    SharedErrors.NOT_AUTHENTICATED,
)
# A route only the team's admins may use: a user outside the team gets the first, the same
# whether the team exists or not; a member who is not an admin, the second.
ADMINS_ONLY = (SharedErrors.NOT_A_TEAM_MEMBER, SharedErrors.NOT_A_TEAM_ADMIN)

USER_ID = Path(description="The `app_user` id of the member.")

CREATE_TEAM_DESCRIPTION = f"""
Creates a team in a single transaction, with these defaults:

- `mode`: `{OperationMode.SUPPORT}` (a human Scrum Master approves Agilina's actions);
- `language`: `{Language.EN}` (English);
- the user who creates it becomes its `{TeamRole.ADMIN}` and is recorded as its creator.

If anything fails, neither the team nor the membership is stored.
"""


@router.post(
    "",
    response_model=CreatedTeamResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a team and become its admin",
    description=CREATE_TEAM_DESCRIPTION,
    responses={
        201: {"description": "Created; `Location` points to the new team"},
        **errors_of(*SIGNED_IN, SharedErrors.VALIDATION, TeamsErrors.INVALID_TEAM_NAME),
    },
)
async def create_team(
    request: CreateTeamRequest,
    response: Response,
    user_id: UUID = Depends(current_user_id),
    handler: CreateTeamAsAdminHandler = Depends(get_create_team_as_admin_handler),
) -> CreatedTeamResponse:
    team_id = await handler.handle(CreateTeamAsAdmin(name=request.name, user_id=user_id))
    response.headers["Location"] = f"{router.prefix}/{team_id}"
    return present_created(team_id)


@router.get(
    "",
    response_model=list[MyTeamResponse],
    summary="The teams of the authenticated user",
    description=(
        "Every team where the user is an active member, with their role in it, ordered by "
        "name ignoring case. Empty when the user has no team."
    ),
    responses=errors_of(*SIGNED_IN),
)
async def list_my_teams(
    user_id: UUID = Depends(current_user_id),
    handler: ListMyTeamsHandler = Depends(get_list_my_teams_handler),
) -> list[MyTeamResponse]:
    views = await handler.handle(ListMyTeams(user_id=user_id))
    return [present_my_team(view) for view in views]


@router.get(
    "/{team_id}",
    response_model=TeamResponse,
    summary="One of the user's teams",
    description=(
        "The team's name, mode and language, and the user's role in it. Only an active "
        "member gets it: any other user receives `403 not_a_team_member`, whether the team "
        "exists or not. A `team_id` that is not a UUID answers `422 validation_error`."
    ),
    responses=errors_of(*SIGNED_IN, SharedErrors.VALIDATION, SharedErrors.NOT_A_TEAM_MEMBER),
)
async def get_team(
    team: TeamContext = Depends(current_team_member),
    handler: GetTeamHandler = Depends(get_get_team_handler),
) -> TeamResponse:
    view = await handler.handle(GetTeam(team_id=team.team_id))
    return present_team(view, team.role)


@router.get(
    "/{team_id}/members",
    response_model=TeamMembersResponse,
    summary="The team's members, for its admins",
    description=(
        "The team's active members with their name, email, internal role and the code of "
        "the role's visible label, ordered by name ignoring case, and the roles an admin can "
        "give with their labels. Each member says why their role cannot change "
        "(`role_change_blocked_by`) or why they cannot be removed (`removal_blocked_by`) "
        "right now, with the same rules the changes enforce. Only an admin of the team gets "
        "it; the role is the one stored in the membership."
    ),
    responses=errors_of(*SIGNED_IN, SharedErrors.VALIDATION, *ADMINS_ONLY),
)
async def list_team_members(
    team: TeamContext = Depends(current_team_admin),
    handler: ListTeamMembersHandler = Depends(get_list_team_members_handler),
) -> TeamMembersResponse:
    members = await handler.handle(ListTeamMembers(team_id=team.team_id))
    return present_members(members)


@router.patch(
    "/{team_id}/members/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
    summary="Give a member another role",
    description=(
        "Changes the internal role of an active member, who may be the admin who asks. "
        "Giving the role the member already has changes nothing. No role changes while the "
        "team has a sprint in progress (`sprint_in_progress`), and the team's only admin "
        "cannot be demoted, also when they ask it themselves (`last_admin`); either way "
        "nothing changes. Only an admin of the team may do it. A body with an unknown field "
        "or an unknown role answers `422 validation_error`."
    ),
    responses={
        204: {"description": "Changed"},
        **errors_of(
            *SIGNED_IN,
            SharedErrors.VALIDATION,
            *ADMINS_ONLY,
            TeamsErrors.MEMBER_NOT_FOUND,
            SharedErrors.TEAM_NOT_FOUND,
            TeamsErrors.SPRINT_IN_PROGRESS,
            TeamsErrors.LAST_ADMIN,
        ),
    },
)
async def change_member_role(
    user_id: Annotated[UUID, USER_ID],
    request: ChangeMemberRoleRequest,
    team: TeamContext = Depends(current_team_admin),
    handler: ChangeMemberRoleHandler = Depends(get_change_member_role_handler),
) -> Response:
    await handler.handle(
        ChangeMemberRole(
            team_id=team.team_id, user_id=user_id, role=request.role, requested_by=team.user_id
        )
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.delete(
    "/{team_id}/members/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
    summary="Remove a member from the team",
    description=(
        "Ends the membership of an active member, who may be the admin who asks: they stop "
        "being called to the team's ceremonies. Their account is not deleted, since it may "
        "belong to other teams, and they can be invited again. The team's only admin cannot "
        "be removed, also when they ask it themselves (`last_admin`); a sprint in progress "
        "does not prevent it. Only an admin of the team may do it."
    ),
    responses={
        204: {"description": "Removed"},
        **errors_of(
            *SIGNED_IN,
            SharedErrors.VALIDATION,
            *ADMINS_ONLY,
            TeamsErrors.MEMBER_NOT_FOUND,
            SharedErrors.TEAM_NOT_FOUND,
            TeamsErrors.LAST_ADMIN,
        ),
    },
)
async def remove_member(
    user_id: Annotated[UUID, USER_ID],
    team: TeamContext = Depends(current_team_admin),
    handler: RemoveMemberHandler = Depends(get_remove_member_handler),
) -> Response:
    await handler.handle(
        RemoveMember(team_id=team.team_id, user_id=user_id, requested_by=team.user_id)
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)
