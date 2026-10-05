"""Errors of the identity domain.

Each one is a business rule that was broken; the presentation layer turns them into
HTTP responses and i18n keys, the domain knows nothing about status codes.
"""

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from agilina_api.shared_kernel import DomainError

if TYPE_CHECKING:
    from agilina_api.identity.domain.invitation import InvitationStatus


class InvalidEmailError(DomainError):
    """The text is not a usable email address."""


class InvalidTokenHashError(DomainError):
    """A token hash must be a SHA-256 digest in hexadecimal."""


class InvalidActivationTokenError(DomainError):
    """The text does not have the shape of an activation token (an altered link)."""


class InvalidFullNameError(DomainError):
    """A person's name cannot be blank."""


class InvitationNotPendingError(DomainError):
    """The invitation can no longer be accepted. Subclasses say why."""

    def __init__(self, invitation_id: UUID, state: "InvitationStatus", at: datetime) -> None:
        super().__init__(f"Invitation {invitation_id} is {state.value} at {at.isoformat()}")
        self.invitation_id = invitation_id
        self.state = state


class InvitationAlreadyUsedError(InvitationNotPendingError):
    """The link was already used."""


class InvitationExpiredError(InvitationNotPendingError):
    """The link expired (seven days after it was issued)."""


class InvitationRevokedError(InvitationNotPendingError):
    """The invitation was cancelled by an admin."""


class PendingInvitationAlreadyExistsError(DomainError):
    """There is already a pending invitation for that email in that team."""


class UserAlreadyExistsError(DomainError):
    """There is already an account with that email or that Keycloak identity (HU-02)."""
