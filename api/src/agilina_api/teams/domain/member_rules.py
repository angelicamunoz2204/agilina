"""What can block changing a member's role or removing them from the team (HU-06).

Pure functions, so the ``Team`` aggregate (which enforces the rules) and the members list
(which tells the interface why a control is disabled) answer from the same source and
the interface never computes a rule.
"""

from enum import StrEnum

from agilina_shared.enums import TeamRole


class MemberChangeBlocker(StrEnum):
    """Why an admin cannot change a member's role or remove them. Stable codes: the
    interface translates them."""

    LAST_ADMIN = "last_admin"
    """The member is the team's only admin: the team cannot be left without one."""
    SPRINT_IN_PROGRESS = "sprint_in_progress"
    """The team has an active sprint: roles do not change while it lasts."""


def is_last_admin(role: TeamRole, admin_count: int) -> bool:
    """Whether a member with ``role`` is the only active admin of a team that has
    ``admin_count`` of them, so demoting or removing them would leave it without one."""
    return role is TeamRole.ADMIN and admin_count <= 1


def role_change_blocker(
    *, role: TeamRole, admin_count: int, sprint_in_progress: bool
) -> MemberChangeBlocker | None:
    """Why the role of a member with ``role`` cannot change, or ``None`` when it can.

    The sprint goes first: while it lasts no role changes, whoever the member is. With
    two roles only, any change of the last admin's role demotes them.
    """
    if sprint_in_progress:
        return MemberChangeBlocker.SPRINT_IN_PROGRESS
    return MemberChangeBlocker.LAST_ADMIN if is_last_admin(role, admin_count) else None


def removal_blocker(*, role: TeamRole, admin_count: int) -> MemberChangeBlocker | None:
    """Why a member with ``role`` cannot be removed, or ``None`` when they can. A sprint
    in progress does not block a removal."""
    return MemberChangeBlocker.LAST_ADMIN if is_last_admin(role, admin_count) else None
