"""Teams API (HU-05): create a team, list the authenticated user's teams and read one.

Every route needs an authenticated user, and that user is always the one behind the
access token (``current_user_id``), never one named in the body. A route about one team
is also kept to its members (``current_team_member``).
"""

from uuid import UUID

from fastapi import APIRouter, Depends, Response, status

from agilina_api.shared.application.access import TeamContext
from agilina_api.shared.presentation.http.access import current_team_member, current_user_id
from agilina_api.shared.presentation.http.errors import ErrorResponse
from agilina_api.teams.application.commands.create_team_as_admin import (
    CreateTeamAsAdmin,
    CreateTeamAsAdminHandler,
)
from agilina_api.teams.application.queries.get_team import GetTeam, GetTeamHandler
from agilina_api.teams.application.queries.list_my_teams import ListMyTeams, ListMyTeamsHandler
from agilina_api.teams.presentation.http.dependencies import (
    get_create_team_as_admin_handler,
    get_get_team_handler,
    get_list_my_teams_handler,
)
from agilina_api.teams.presentation.http.presenters import (
    present_created,
    present_my_team,
    present_team,
)
from agilina_api.teams.presentation.http.schemas import (
    CreatedTeamResponse,
    CreateTeamRequest,
    MyTeamResponse,
    TeamResponse,
)
from agilina_shared.enums import Language, OperationMode, TeamRole

router = APIRouter(prefix="/v1/teams", tags=["teams"])

NOT_AUTHENTICATED = {
    "model": ErrorResponse,
    "description": "No access token, or one that does not identify a user (`not_authenticated`)",
}

NOT_A_TEAM_MEMBER = {
    "model": ErrorResponse,
    "description": "The user is not an active member of the team: it is someone else's, "
    "they were removed from it, or it does not exist (`not_a_team_member`)",
}

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
        401: NOT_AUTHENTICATED,
        422: {
            "model": ErrorResponse,
            "description": "The name is blank or too long once trimmed (`invalid_team_name`). "
            "A malformed body (no name, an unknown field) answers with FastAPI's validation "
            "format instead",
        },
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
    responses={401: NOT_AUTHENTICATED},
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
        "exists or not. A `team_id` that is not a UUID answers `422` with FastAPI's "
        "validation format."
    ),
    responses={401: NOT_AUTHENTICATED, 403: NOT_A_TEAM_MEMBER},
)
async def get_team(
    team: TeamContext = Depends(current_team_member),
    handler: GetTeamHandler = Depends(get_get_team_handler),
) -> TeamResponse:
    view = await handler.handle(GetTeam(team_id=team.team_id))
    return present_team(view, team.role)
