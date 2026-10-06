"""Invitations API.

``router`` (HU-02): check a link, activate the account, ask for a new link. Public on
purpose: the person has no account yet, and the unguessable token in the body is what
authorizes them. Nothing here is cached (it carries tokens and passwords).

``team_invitations_router`` (HU-06): an admin invites a person to their team. It lives in
identity, which owns invitations and accounts, under the team's path; only the team's
admins reach it (``current_team_admin``).
"""

from fastapi import APIRouter, Depends, Response, status
from fastapi.responses import JSONResponse

from agilina_api.identity.application.commands.activate_account import (
    ActivateAccount,
    ActivateAccountHandler,
)
from agilina_api.identity.application.commands.invite_to_team import (
    InviteToTeam,
    InviteToTeamHandler,
)
from agilina_api.identity.application.commands.request_new_invitation import (
    RequestNewInvitation,
    RequestNewInvitationHandler,
)
from agilina_api.identity.application.queries.get_invitation_status import (
    GetInvitationStatus,
    GetInvitationStatusHandler,
)
from agilina_api.identity.domain.invitation import InvitationStatus
from agilina_api.identity.presentation.http.dependencies import (
    get_activate_account_handler,
    get_invitation_status_handler,
    get_invite_to_team_handler,
    get_request_new_invitation_handler,
)
from agilina_api.identity.presentation.http.presenters import present_activated, present_status
from agilina_api.identity.presentation.http.schemas import (
    ActivatedAccountResponse,
    ActivateRequest,
    InvitationStatusResponse,
    InviteToTeamRequest,
    InviteToTeamResponse,
    RequestedResponse,
    TokenRequest,
)
from agilina_api.shared.application.access import TeamContext
from agilina_api.shared.presentation.http.access import current_team_admin
from agilina_api.shared.presentation.http.errors import ErrorResponse, error_response


def _no_store(response: Response) -> None:
    response.headers["Cache-Control"] = "no-store"


router = APIRouter(
    prefix="/v1/invitations", tags=["invitations"], dependencies=[Depends(_no_store)]
)

GONE = {
    InvitationStatus.ACCEPTED: "invitation_used",
    InvitationStatus.EXPIRED: "invitation_expired",
    InvitationStatus.REVOKED: "invitation_revoked",
}


@router.post(
    "/status",
    response_model=InvitationStatusResponse,
    summary="What the activation page shows about a link",
    responses={
        404: {"model": ErrorResponse, "description": "The link was altered or never existed"},
        410: {"model": ErrorResponse, "description": "The link was used, expired or revoked"},
    },
)
async def invitation_status(
    request: TokenRequest,
    handler: GetInvitationStatusHandler = Depends(get_invitation_status_handler),
) -> InvitationStatusResponse | JSONResponse:
    view = await handler.handle(GetInvitationStatus(token=request.token))
    if view.status is not InvitationStatus.PENDING:
        code = GONE[view.status]
        return error_response(status.HTTP_410_GONE, code, code.replace("_", " "))
    return present_status(view)


@router.post(
    "/activate",
    response_model=ActivatedAccountResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Choose a password and activate the account",
    responses={
        404: {"model": ErrorResponse, "description": "The link was altered or never existed"},
        409: {"model": ErrorResponse, "description": "That email already has an account"},
        410: {"model": ErrorResponse, "description": "The link was used, expired or revoked"},
        422: {
            "model": ErrorResponse,
            "description": "The password does not match or breaks the policy",
        },
        503: {"model": ErrorResponse, "description": "The identity provider is unavailable"},
    },
)
async def activate_account(
    request: ActivateRequest,
    handler: ActivateAccountHandler = Depends(get_activate_account_handler),
) -> ActivatedAccountResponse | JSONResponse:
    if request.password != request.confirmation:
        return error_response(422, "password_mismatch", "password mismatch")
    account = await handler.handle(ActivateAccount(token=request.token, password=request.password))
    return present_activated(account)


@router.post(
    "/request-new",
    response_model=RequestedResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Ask the team's admins for a new invitation",
    responses={
        404: {"model": ErrorResponse, "description": "The link was altered or never existed"},
        409: {"model": ErrorResponse, "description": "The link still works, or nobody can be told"},
        502: {"model": ErrorResponse, "description": "The email could not be sent"},
    },
)
async def request_new_invitation(
    request: TokenRequest,
    handler: RequestNewInvitationHandler = Depends(get_request_new_invitation_handler),
) -> RequestedResponse:
    await handler.handle(RequestNewInvitation(token=request.token))
    return RequestedResponse()


team_invitations_router = APIRouter(prefix="/v1/teams", tags=["teams"])

INVITE_TO_TEAM_DESCRIPTION = """
Invites a person to the team with a role (`member` by default). What happens depends on
the email:

- **no account in Agilina:** an invitation is stored and its activation link (single use,
  valid for seven days) is e-mailed; activating it puts the person in the team with the
  chosen role (`invitation_sent`);
- **an existing account:** the person joins the team right away with the chosen role and
  gets a notice without an activation link (`member_added`);
- **already an active member:** refused with `409 already_a_team_member`; nothing is
  stored or sent.

A pending invitation of that email to the team stops working: the new one replaces it.
The email is sent before anything is stored, so if the mail server refuses it the answer
is `502 mail_unavailable` and nothing changes. Only an admin of the team may invite.
"""


@team_invitations_router.post(
    "/{team_id}/invitations",
    response_model=InviteToTeamResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Invite a person to the team",
    description=INVITE_TO_TEAM_DESCRIPTION,
    responses={
        201: {"description": "Invited: an invitation was sent or the account joined the team"},
        401: {
            "model": ErrorResponse,
            "description": "No access token, or one that does not identify a user "
            "(`not_authenticated`)",
        },
        403: {
            "model": ErrorResponse,
            "description": "The user is not an active member of the team "
            "(`not_a_team_member`), or is a member but not one of its admins "
            "(`not_a_team_admin`)",
        },
        404: {"model": ErrorResponse, "description": "The team does not exist (`team_not_found`)"},
        409: {
            "model": ErrorResponse,
            "description": "The person is already an active member (`already_a_team_member`), "
            "their account is disabled (`account_disabled`), or another invitation to them "
            "was being issued at the same moment (`pending_invitation_exists`)",
        },
        422: {
            "model": ErrorResponse,
            "description": "The email is malformed (`invalid_email`) or the name blank "
            "(`invalid_full_name`). A malformed body (a missing or unknown field, an unknown "
            "role) answers with FastAPI's validation format instead",
        },
        502: {"model": ErrorResponse, "description": "The email could not be sent"},
    },
)
async def invite_to_team(
    request: InviteToTeamRequest,
    team: TeamContext = Depends(current_team_admin),
    handler: InviteToTeamHandler = Depends(get_invite_to_team_handler),
) -> InviteToTeamResponse:
    outcome = await handler.handle(
        InviteToTeam(
            team_id=team.team_id,
            inviter_user_id=team.user_id,
            inviter_membership_id=team.membership_id,
            email=request.email,
            full_name=request.full_name,
            role=request.role,
        )
    )
    return InviteToTeamResponse(outcome=outcome)
