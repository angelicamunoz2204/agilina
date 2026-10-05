"""Turn application results into response models."""

from agilina_api.identity.application.dtos import ActivatedAccount, InvitationStatusView
from agilina_api.identity.presentation.http.schemas import (
    ActivatedAccountResponse,
    InvitationStatusResponse,
)


def present_status(view: InvitationStatusView) -> InvitationStatusResponse:
    return InvitationStatusResponse(
        email=view.email,
        full_name=view.full_name,
        role=view.role,
        status=view.status,
        expires_at=view.expires_at,
    )


def present_activated(account: ActivatedAccount) -> ActivatedAccountResponse:
    return ActivatedAccountResponse(
        email=account.email.value, team_id=account.team_id, role=account.role
    )
