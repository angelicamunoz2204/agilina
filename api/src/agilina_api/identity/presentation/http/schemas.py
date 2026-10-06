"""Request and response models of the invitations API."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from agilina_api.identity.application.dtos import TeamInvitationOutcome
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


class InviteToTeamRequest(BaseModel):
    """Who to invite and with which role. The team comes from the path and the admin who
    invites from the access token, never from the body."""

    # An unknown field (``team_id``, ``created_by``…) is refused, not silently ignored.
    model_config = ConfigDict(extra="forbid")

    full_name: str = Field(
        max_length=200,
        description="The person's name. A blank one answers `422 invalid_full_name`.",
        examples=["Laura Méndez"],
    )
    email: str = Field(
        max_length=320,
        description="Where the invitation goes. A malformed one answers `422 invalid_email`.",
        examples=["laura@example.com"],
    )
    role: TeamRole = Field(
        default=TeamRole.MEMBER,
        description=f"The role the person gets in the team. `{TeamRole.MEMBER}` by default.",
    )


class InviteToTeamResponse(BaseModel):
    outcome: TeamInvitationOutcome = Field(
        description=(
            f"`{TeamInvitationOutcome.INVITATION_SENT}`: the email had no account and got an "
            "invitation with its activation link. "
            f"`{TeamInvitationOutcome.MEMBER_ADDED}`: the email already had an account, which "
            "joined the team and got a notice without a link."
        )
    )
