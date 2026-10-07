from enum import StrEnum


class MemberChangeBlocker(StrEnum):
    """Why an admin cannot change a member's role or remove them. Stable codes: the
    interface translates them."""

    LAST_ADMIN = "last_admin"
    """The member is the team's only admin: the team cannot be left without one."""
    SPRINT_IN_PROGRESS = "sprint_in_progress"
    """The team has an active sprint: roles do not change while it lasts."""
