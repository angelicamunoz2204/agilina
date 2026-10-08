from agilina_api.teams.application.dtos import MemberContact, MemberRecord, MemberView
from agilina_api.teams.domain.member_rules import removal_blocker, role_change_blocker
from agilina_shared import role_label
from agilina_shared.enums import OperationMode


def build_member_view(
    record: MemberRecord,
    contact: MemberContact,
    *,
    admin_count: int,
    has_active_sprint: bool,
    mode: OperationMode,
) -> MemberView:
    """One member as the interface shows them: the contact data from identity, the role with
    its label in this team, and why their role cannot change or they cannot be removed, with
    the same rules the commands enforce."""
    return MemberView(
        user_id=record.user_id,
        full_name=contact.full_name,
        email=contact.email,
        role=record.role,
        label=role_label(record.role, mode),
        joined_at=record.joined_at,
        role_change_blocked_by=role_change_blocker(
            role=record.role, admin_count=admin_count, sprint_in_progress=has_active_sprint
        ),
        removal_blocked_by=removal_blocker(role=record.role, admin_count=admin_count),
    )
