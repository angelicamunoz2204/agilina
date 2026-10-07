from enum import StrEnum


class MembershipStatus(StrEnum):
    """The values match the PostgreSQL ``membership_status`` enum."""

    ACTIVE = "active"
    REMOVED = "removed"
