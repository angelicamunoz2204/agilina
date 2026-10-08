from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from agilina_shared.enums import RoleLabel, TeamRole


class MeResponse(BaseModel):
    """The caller as a member of one team: what the app header shows."""

    user_id: UUID
    full_name: str
    email: str
    role: TeamRole = Field(description="The caller's internal role in the team.")
    label: RoleLabel = Field(
        description="The code of the label the interface shows for that role in this team."
    )
    joined_at: datetime = Field(description="Since when the caller is in the team (UTC).")
