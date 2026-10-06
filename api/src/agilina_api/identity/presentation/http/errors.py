"""The identity errors and the HTTP response each one becomes.

The composition root registers this table in the single handler of
``shared.presentation.http.errors``.
"""

from typing import cast

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
from agilina_api.shared.presentation.http.errors import ErrorMapping


def _password_policy_reasons(error: Exception) -> list[str]:
    # The mapping below registers it only for PasswordPolicyError.
    return list(cast(PasswordPolicyError, error).reasons)


IDENTITY_ERRORS: tuple[ErrorMapping, ...] = (
    ErrorMapping(InvitationNotFoundError, 404, "invitation_not_found"),
    ErrorMapping(InvitationAlreadyUsedError, 410, "invitation_used"),
    ErrorMapping(InvitationExpiredError, 410, "invitation_expired"),
    ErrorMapping(InvitationRevokedError, 410, "invitation_revoked"),
    ErrorMapping(AccountAlreadyExistsError, 409, "account_already_exists"),
    ErrorMapping(InvitationStillValidError, 409, "invitation_still_valid"),
    ErrorMapping(NoAdminsToNotifyError, 409, "no_admins_to_notify"),
    ErrorMapping(PasswordPolicyError, 422, "password_policy", reasons=_password_policy_reasons),
    ErrorMapping(IdentityProviderUnavailableError, 503, "identity_provider_unavailable"),
)
