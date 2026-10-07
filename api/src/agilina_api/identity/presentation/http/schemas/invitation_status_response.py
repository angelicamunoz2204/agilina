from datetime import datetime

from pydantic import BaseModel

from agilina_api.identity.domain.invitation import InvitationStatus
from agilina_shared.enums import TeamRole


class InvitationStatusResponse(BaseModel):
    email: str
    full_name: str
    role: TeamRole
    status: InvitationStatus
    expires_at: datetime
