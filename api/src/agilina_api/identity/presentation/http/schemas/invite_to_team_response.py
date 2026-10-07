from pydantic import BaseModel, Field

from agilina_api.identity.application.dtos import TeamInvitationOutcome


class InviteToTeamResponse(BaseModel):
    outcome: TeamInvitationOutcome = Field(
        description=(
            f"`{TeamInvitationOutcome.INVITATION_SENT}`: the email had no account and got an "
            "invitation with its activation link. "
            f"`{TeamInvitationOutcome.MEMBER_ADDED}`: the email already had an account, which "
            "joined the team and got a notice without a link."
        )
    )
