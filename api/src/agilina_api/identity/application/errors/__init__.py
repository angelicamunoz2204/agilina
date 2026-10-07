"""Errors of the identity use cases: what can go wrong when someone follows a link."""

from agilina_api.identity.application.errors.account_already_exists_error import (
    AccountAlreadyExistsError,
)
from agilina_api.identity.application.errors.identity_provider_unavailable_error import (
    IdentityProviderUnavailableError,
)
from agilina_api.identity.application.errors.invitation_not_found_error import (
    InvitationNotFoundError,
)
from agilina_api.identity.application.errors.invitation_still_valid_error import (
    InvitationStillValidError,
)
from agilina_api.identity.application.errors.no_admins_to_notify_error import NoAdminsToNotifyError
from agilina_api.identity.application.errors.password_policy_error import PasswordPolicyError

__all__ = [
    "AccountAlreadyExistsError",
    "IdentityProviderUnavailableError",
    "InvitationNotFoundError",
    "InvitationStillValidError",
    "NoAdminsToNotifyError",
    "PasswordPolicyError",
]
