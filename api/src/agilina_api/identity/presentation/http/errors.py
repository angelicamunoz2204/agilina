"""Turn the identity errors into HTTP responses.

The domain knows nothing about status codes: this table is the only place that says that
an expired link is a ``410`` or a refused password a ``422``.
"""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from agilina_api.identity.application.errors import (
    AccountAlreadyExistsError,
    IdentityProviderUnavailableError,
    InvitationNotFoundError,
    InvitationStillValidError,
    NoAdminsToNotifyError,
    PasswordPolicyError,
)
from agilina_api.identity.domain.errors import (
    InvitationAlreadyUsedError,
    InvitationExpiredError,
    InvitationRevokedError,
)
from agilina_api.identity.presentation.http.schemas import ErrorResponse
from agilina_api.shared.application.ports import MailDeliveryError

ERRORS: tuple[tuple[type[Exception], int, str], ...] = (
    (InvitationNotFoundError, 404, "invitation_not_found"),
    (InvitationAlreadyUsedError, 410, "invitation_used"),
    (InvitationExpiredError, 410, "invitation_expired"),
    (InvitationRevokedError, 410, "invitation_revoked"),
    (AccountAlreadyExistsError, 409, "account_already_exists"),
    (InvitationStillValidError, 409, "invitation_still_valid"),
    (NoAdminsToNotifyError, 409, "no_admins_to_notify"),
    (PasswordPolicyError, 422, "password_policy"),
    (MailDeliveryError, 502, "mail_unavailable"),
    (IdentityProviderUnavailableError, 503, "identity_provider_unavailable"),
)


def error_response(
    status: int, code: str, detail: str, reasons: list[str] | None = None
) -> JSONResponse:
    body = ErrorResponse(code=code, detail=detail, reasons=reasons)
    return JSONResponse(
        status_code=status,
        content=body.model_dump(exclude_none=True),
        headers={"Cache-Control": "no-store"},
    )


def register_error_handlers(app: FastAPI) -> None:
    for error_type, status, code in ERRORS:

        async def handle(
            request: Request, error: Exception, status: int = status, code: str = code
        ) -> JSONResponse:
            reasons = list(error.reasons) if isinstance(error, PasswordPolicyError) else None
            # The detail is generic on purpose: the messages of the errors name people and
            # invitations, and the response must not.
            return error_response(status, code, code.replace("_", " "), reasons)

        app.add_exception_handler(error_type, handle)
