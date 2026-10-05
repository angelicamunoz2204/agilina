"""Request and response models of the invitations API."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from agilina_api.identity.domain.invitation import InvitationStatus
from agilina_shared.enums import TeamRole


class TokenRequest(BaseModel):
    """The token travels in the body, never in the URL: a URL ends up in logs."""

    token: str = Field(max_length=200)


class ActivateRequest(BaseModel):
    token: str = Field(max_length=200)
    password: str = Field(min_length=1, max_length=256)
    confirmation: str = Field(max_length=256)


class InvitationStatusResponse(BaseModel):
    email: str
    full_name: str
    role: TeamRole
    status: InvitationStatus
    expires_at: datetime


class ActivatedAccountResponse(BaseModel):
    email: str
    team_id: UUID
    role: TeamRole


class RequestedResponse(BaseModel):
    status: str = "requested"


class ErrorResponse(BaseModel):
    """Every failure answers with a stable ``code`` the web turns into a message in the
    person's language; ``detail`` is for developers."""

    code: str
    detail: str
    reasons: list[str] | None = None
