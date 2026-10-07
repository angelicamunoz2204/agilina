from pydantic import BaseModel, ConfigDict, Field

from agilina_shared.enums import TeamRole


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
