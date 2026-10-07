from agilina_shared.enums import TeamRole


def is_last_admin(role: TeamRole, admin_count: int) -> bool:
    """Whether a member with ``role`` is the only active admin of a team that has
    ``admin_count`` of them, so demoting or removing them would leave it without one."""
    return role is TeamRole.ADMIN and admin_count <= 1
