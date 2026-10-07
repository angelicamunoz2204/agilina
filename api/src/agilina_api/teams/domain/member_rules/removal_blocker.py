from agilina_api.teams.domain.member_rules.is_last_admin import is_last_admin
from agilina_api.teams.domain.member_rules.member_change_blocker import MemberChangeBlocker
from agilina_shared.enums import TeamRole


def removal_blocker(*, role: TeamRole, admin_count: int) -> MemberChangeBlocker | None:
    """Why a member with ``role`` cannot be removed, or ``None`` when they can. A sprint
    in progress does not block a removal."""
    return MemberChangeBlocker.LAST_ADMIN if is_last_admin(role, admin_count) else None
