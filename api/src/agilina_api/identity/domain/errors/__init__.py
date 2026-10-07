"""Errors of the identity domain.

Each one is a business rule that was broken; the presentation layer turns them into
HTTP responses and i18n keys, the domain knows nothing about status codes.
"""

from agilina_api.identity.domain.errors.account_disabled_error import AccountDisabledError
from agilina_api.identity.domain.errors.already_team_member_error import AlreadyTeamMemberError
from agilina_api.identity.domain.errors.invalid_activation_token_error import (
    InvalidActivationTokenError,
)
from agilina_api.identity.domain.errors.invalid_email_error import InvalidEmailError
from agilina_api.identity.domain.errors.invalid_full_name_error import InvalidFullNameError
from agilina_api.identity.domain.errors.invalid_token_hash_error import InvalidTokenHashError
from agilina_api.identity.domain.errors.invitation_already_used_error import (
    InvitationAlreadyUsedError,
)
from agilina_api.identity.domain.errors.invitation_expired_error import InvitationExpiredError
from agilina_api.identity.domain.errors.invitation_not_pending_error import (
    InvitationNotPendingError,
)
from agilina_api.identity.domain.errors.invitation_revoked_error import InvitationRevokedError
from agilina_api.identity.domain.errors.pending_invitation_already_exists_error import (
    PendingInvitationAlreadyExistsError,
)
from agilina_api.identity.domain.errors.unknown_team_error import UnknownTeamError
from agilina_api.identity.domain.errors.user_already_exists_error import UserAlreadyExistsError

__all__ = [
    "AccountDisabledError",
    "AlreadyTeamMemberError",
    "InvalidActivationTokenError",
    "InvalidEmailError",
    "InvalidFullNameError",
    "InvalidTokenHashError",
    "InvitationAlreadyUsedError",
    "InvitationExpiredError",
    "InvitationNotPendingError",
    "InvitationRevokedError",
    "PendingInvitationAlreadyExistsError",
    "UnknownTeamError",
    "UserAlreadyExistsError",
]
