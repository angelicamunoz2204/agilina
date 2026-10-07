"""Invitations API (HU-02): check a link, activate the account, ask for a new link.

Public on purpose: the person has no account yet, and the unguessable token in the body is
what authorizes them. Nothing here is cached (it carries tokens and passwords).
"""

from fastapi import APIRouter, Depends, Response, status

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
from agilina_api.identity.presentation.http.errors import IdentityErrors
from agilina_api.identity.presentation.http.presenters import present_activated, present_status
from agilina_api.identity.presentation.http.schemas import (
    ActivatedAccountResponse,
    ActivateRequest,
    InvitationStatusResponse,
    RequestedResponse,
    TokenRequest,
)
from agilina_api.shared.presentation.http.api_error import ApiException, SharedErrors
from agilina_api.shared.presentation.http.error_schema import errors_of


def _no_store(response: Response) -> None:
    response.headers["Cache-Control"] = "no-store"


router = APIRouter(
    prefix="/v1/invitations", tags=["invitations"], dependencies=[Depends(_no_store)]
)

GONE = {
    InvitationStatus.ACCEPTED: IdentityErrors.INVITATION_USED,
    InvitationStatus.EXPIRED: IdentityErrors.INVITATION_EXPIRED,
    InvitationStatus.REVOKED: IdentityErrors.INVITATION_REVOKED,
}

TENANT = (SharedErrors.TENANT_REQUIRED, SharedErrors.TENANT_NOT_FOUND)
LINK_GONE = (
    IdentityErrors.INVITATION_USED,
    IdentityErrors.INVITATION_EXPIRED,
    IdentityErrors.INVITATION_REVOKED,
)


@router.post(
    "/status",
    response_model=InvitationStatusResponse,
    summary="What the activation page shows about a link",
    responses=errors_of(
        *TENANT, SharedErrors.VALIDATION, IdentityErrors.INVITATION_NOT_FOUND, *LINK_GONE
    ),
)
async def invitation_status(
    request: TokenRequest,
    handler: GetInvitationStatusHandler = Depends(get_invitation_status_handler),
) -> InvitationStatusResponse:
    view = await handler.handle(GetInvitationStatus(token=request.token))
    if view.status is not InvitationStatus.PENDING:
        raise ApiException(GONE[view.status])
    return present_status(view)


@router.post(
    "/activate",
    response_model=ActivatedAccountResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Choose a password and activate the account",
    responses=errors_of(
        *TENANT,
        SharedErrors.VALIDATION,
        IdentityErrors.INVITATION_NOT_FOUND,
        IdentityErrors.ACCOUNT_ALREADY_EXISTS,
        *LINK_GONE,
        IdentityErrors.PASSWORD_MISMATCH,
        IdentityErrors.PASSWORD_POLICY,
        IdentityErrors.IDENTITY_PROVIDER_UNAVAILABLE,
    ),
)
async def activate_account(
    request: ActivateRequest,
    handler: ActivateAccountHandler = Depends(get_activate_account_handler),
) -> ActivatedAccountResponse:
    if request.password != request.confirmation:
        raise ApiException(IdentityErrors.PASSWORD_MISMATCH)
    account = await handler.handle(ActivateAccount(token=request.token, password=request.password))
    return present_activated(account)


@router.post(
    "/request-new",
    response_model=RequestedResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Ask the team's admins for a new invitation",
    responses=errors_of(
        *TENANT,
        SharedErrors.VALIDATION,
        IdentityErrors.INVITATION_NOT_FOUND,
        IdentityErrors.INVITATION_STILL_VALID,
        IdentityErrors.NO_ADMINS_TO_NOTIFY,
        SharedErrors.MAIL_UNAVAILABLE,
    ),
)
async def request_new_invitation(
    request: TokenRequest,
    handler: RequestNewInvitationHandler = Depends(get_request_new_invitation_handler),
) -> RequestedResponse:
    await handler.handle(RequestNewInvitation(token=request.token))
    return RequestedResponse()
