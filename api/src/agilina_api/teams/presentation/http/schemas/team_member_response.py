from uuid import UUID

from pydantic import BaseModel, Field

from agilina_api.teams.domain.member_rules import MemberChangeBlocker
from agilina_shared.enums import TeamRole


class TeamMemberResponse(BaseModel):
    user_id: UUID
    full_name: str
    email: str
    role: TeamRole = Field(description="The member's internal role: what authorization uses.")
    label: str = Field(description="The code of the role's visible label (see `roles`).")
    role_change_blocked_by: MemberChangeBlocker | None = Field(
        description=(
            "Why the member's role cannot change now, or `null` when it can: "
            f"`{MemberChangeBlocker.SPRINT_IN_PROGRESS}` while the team has a sprint in "
            f"progress (it comes first), `{MemberChangeBlocker.LAST_ADMIN}` when the member is "
            "the team's only admin. The interface disables the control and shows the reason."
        )
    )
    removal_blocked_by: MemberChangeBlocker | None = Field(
        description=(
            "Why the member cannot be removed now, or `null` when they can: "
            f"`{MemberChangeBlocker.LAST_ADMIN}` when the member is the team's only admin. A "
            "sprint in progress does not block a removal."
        )
    )
