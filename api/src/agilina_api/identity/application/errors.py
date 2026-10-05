"""Errors of the identity use cases: what can go wrong when someone follows a link."""

from agilina_api.shared_kernel import DomainError


class InvitationNotFoundError(DomainError):
    """No invitation has that token: the link was altered or never existed."""


class InvitationStillValidError(DomainError):
    """A new invitation was requested but the current link still works."""


class AccountAlreadyExistsError(DomainError):
    """The email already has an account (HU-02). Linking it to another team is HU-06."""


class PasswordPolicyError(DomainError):
    """The identity provider refused the password.

    ``reasons`` are stable codes the interface turns into messages (``min_length``,
    ``not_username``, ``not_email``, ``other``).
    """

    def __init__(self, reasons: tuple[str, ...]) -> None:
        super().__init__("The password does not meet the policy: " + ", ".join(reasons))
        self.reasons = reasons


class NoAdminsToNotifyError(DomainError):
    """The team has nobody to tell that a new invitation was requested."""


class IdentityProviderUnavailableError(Exception):
    """The identity provider did not answer or failed. Not a business rule: it is an
    outage, and the interface reports it as such."""
