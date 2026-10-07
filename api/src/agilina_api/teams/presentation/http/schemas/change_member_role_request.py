from pydantic import BaseModel, ConfigDict, Field

from agilina_shared.enums import TeamRole


class ChangeMemberRoleRequest(BaseModel):
    """Only the new role: the team and the member come from the path."""

    # An unknown field (``team_id``, ``user_id``…) is refused, not silently ignored.
    model_config = ConfigDict(extra="forbid")

    role: TeamRole = Field(description="The member's new internal role in the team.")
