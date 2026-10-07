"""The identity errors and the HTTP response each one becomes.

``IdentityErrors`` is the catalog; ``IDENTITY_ERRORS`` pairs each domain exception with an
entry, and the composition root registers it in ``shared.presentation.http.error_handlers``.
"""

from typing import Any, cast

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
from agilina_api.shared.presentation.http.api_error import ApiError
from agilina_api.shared.presentation.http.error_handlers import ErrorMapping


class IdentityErrors:
    INVITATION_NOT_FOUND = ApiError(
        404, "invitation_not_found", "The link was altered or never existed."
    )
    INVITATION_USED = ApiError(410, "invitation_used", "The invitation was already used.")
    INVITATION_EXPIRED = ApiError(410, "invitation_expired", "The invitation expired.")
    INVITATION_REVOKED = ApiError(410, "invitation_revoked", "The invitation was revoked.")
    ACCOUNT_ALREADY_EXISTS = ApiError(
        409, "account_already_exists", "That email already has an account."
    )
    INVITATION_STILL_VALID = ApiError(409, "invitation_still_valid", "The invitation still works.")
    NO_ADMINS_TO_NOTIFY = ApiError(409, "no_admins_to_notify", "The team has no admin to tell.")
    PASSWORD_POLICY = ApiError(422, "password_policy", "The password breaks the policy.")
    PASSWORD_MISMATCH = ApiError(
        422, "password_mismatch", "The password and its confirmation differ."
    )
    IDENTITY_PROVIDER_UNAVAILABLE = ApiError(
        503, "identity_provider_unavailable", "The identity provider is unavailable."
    )


def _password_policy_details(error: Exception) -> dict[str, Any]:
    # The mapping below registers it only for PasswordPolicyError.
    return {"reasons": list(cast(PasswordPolicyError, error).reasons)}


IDENTITY_ERRORS: tuple[ErrorMapping, ...] = (
    ErrorMapping(InvitationNotFoundError, IdentityErrors.INVITATION_NOT_FOUND),
    ErrorMapping(InvitationAlreadyUsedError, IdentityErrors.INVITATION_USED),
    ErrorMapping(InvitationExpiredError, IdentityErrors.INVITATION_EXPIRED),
    ErrorMapping(InvitationRevokedError, IdentityErrors.INVITATION_REVOKED),
    ErrorMapping(AccountAlreadyExistsError, IdentityErrors.ACCOUNT_ALREADY_EXISTS),
    ErrorMapping(InvitationStillValidError, IdentityErrors.INVITATION_STILL_VALID),
    ErrorMapping(NoAdminsToNotifyError, IdentityErrors.NO_ADMINS_TO_NOTIFY),
    ErrorMapping(
        PasswordPolicyError, IdentityErrors.PASSWORD_POLICY, details=_password_policy_details
    ),
    ErrorMapping(IdentityProviderUnavailableError, IdentityErrors.IDENTITY_PROVIDER_UNAVAILABLE),
)
