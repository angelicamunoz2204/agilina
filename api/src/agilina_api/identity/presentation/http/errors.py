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
    AccountDisabledError,
    AlreadyTeamMemberError,
    InvalidEmailError,
    InvalidFullNameError,
    InvitationAlreadyUsedError,
    InvitationExpiredError,
    InvitationRevokedError,
    PendingInvitationAlreadyExistsError,
    UnknownTeamError,
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
    ErrorMapping(InvalidEmailError, 422, "invalid_email"),
    ErrorMapping(InvalidFullNameError, 422, "invalid_full_name"),
    ErrorMapping(AlreadyTeamMemberError, 409, "already_a_team_member"),
    ErrorMapping(AccountDisabledError, 409, "account_disabled"),
    # Only two invitations to the same person at the same instant get here: the second
    # one finds the index already taken by the first.
    ErrorMapping(PendingInvitationAlreadyExistsError, 409, "pending_invitation_exists"),
    ErrorMapping(UnknownTeamError, 404, "team_not_found"),
)
