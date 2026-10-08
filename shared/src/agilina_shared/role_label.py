"""The visible label of a role (HU-04)."""

from agilina_shared.enums import OperationMode, RoleLabel, TeamRole


def role_label(role: TeamRole, mode: OperationMode) -> RoleLabel:
    """The label the interface shows for ``role`` in a team that works in ``mode``.

    A member is always a member. The admin is the Scrum Master while a human supervises
    Agilina (support mode) and the administrator once the team runs on its own. The
    permissions are the same in both: only whether Agilina asks for approvals changes.
    """
    if role is TeamRole.MEMBER:
        return RoleLabel.MEMBER
    return RoleLabel.SCRUM_MASTER if mode is OperationMode.SUPPORT else RoleLabel.ADMIN
