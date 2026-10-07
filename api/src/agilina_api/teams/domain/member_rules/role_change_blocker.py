from agilina_api.teams.domain.member_rules.is_last_admin import is_last_admin
from agilina_api.teams.domain.member_rules.member_change_blocker import MemberChangeBlocker
from agilina_shared.enums import TeamRole


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
