"""Invitations API (HU-02): check a link, activate the account, ask for a new link.

Public on purpose: the person has no account yet, and the unguessable token in the body is
what authorizes them. Nothing here is cached (it carries tokens and passwords).
"""

from fastapi import APIRouter, Depends, Response, status
from fastapi.responses import JSONResponse

from agilina_api.identity.application.commands.activate_account import (
    ActivateAccount,
    ActivateAccountHandler,
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
    get_request_new_invitation_handler,
)
from agilina_api.identity.presentation.http.errors import error_response
from agilina_api.identity.presentation.http.presenters import present_activated, present_status
from agilina_api.identity.presentation.http.schemas import (
    ActivatedAccountResponse,
    ActivateRequest,
    ErrorResponse,
    InvitationStatusResponse,
    RequestedResponse,
    TokenRequest,
)


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
