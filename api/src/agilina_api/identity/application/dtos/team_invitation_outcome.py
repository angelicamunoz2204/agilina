from enum import StrEnum


class TeamInvitationOutcome(StrEnum):
    """What inviting a person to a team did (HU-06)."""

    INVITATION_SENT = "invitation_sent"
    """They had no account: they got an invitation with its activation link."""
    MEMBER_ADDED = "member_added"
    """They already had an account: they joined the team and got a notice, without a link."""
