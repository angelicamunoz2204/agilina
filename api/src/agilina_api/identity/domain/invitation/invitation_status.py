from enum import StrEnum


class InvitationStatus(StrEnum):
    """The values match the PostgreSQL ``invitation_status`` enum."""

    PENDING = "pending"
    ACCEPTED = "accepted"
    EXPIRED = "expired"
    REVOKED = "revoked"
