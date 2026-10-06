"""Request and response models of the teams API."""

from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from agilina_api.teams.domain.member_rules import MemberChangeBlocker
from agilina_api.teams.domain.team_name import MAX_LENGTH
from agilina_shared.enums import Language, OperationMode, TeamRole


class CreateTeamRequest(BaseModel):
    """Only the name: whoever creates the team comes from the access token, and every new
    team starts with the same mode and language."""

    # An unknown field (``created_by``, ``mode``…) is refused, not silently ignored.
    model_config = ConfigDict(extra="forbid")

    name: str = Field(
        description=(
            "The team's name. Surrounding spaces are trimmed; a blank name, or one longer "
            f"than {MAX_LENGTH} characters once trimmed, answers `422 invalid_team_name`. "
            "Names may repeat: a team is identified by its id."
        ),
        examples=["Atlas"],
    )


class CreatedTeamResponse(BaseModel):
    id: UUID


class MyTeamResponse(BaseModel):
    id: UUID
    name: str
    role: TeamRole = Field(description="The user's role in that team.")


class TeamResponse(BaseModel):
    id: UUID
    name: str
    mode: OperationMode = Field(
        description=(
            f"How Agilina works in the team. A new team starts in `{OperationMode.SUPPORT}`: "
            "a human Scrum Master approves Agilina's actions."
        )
    )
    language: Language = Field(
        description=f"The team's language, as a code. A new team starts in `{Language.EN}`."
    )
    role: TeamRole = Field(description="The role in the team of the user who asks.")


class ChangeMemberRoleRequest(BaseModel):
    """Only the new role: the team and the member come from the path."""

    model_config = ConfigDict(extra="forbid")

    role: TeamRole = Field(description="The member's new internal role in the team.")


class RoleOptionResponse(BaseModel):
    role: TeamRole
    label: str = Field(
        description=(
            "The code of the label the interface shows for the role; the interface translates "
            "it. Today it is the role itself (`admin` or `member`); HU-04 derives it from the "
            "role and the team's mode."
        )
    )


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


class TeamMembersResponse(BaseModel):
    roles: list[RoleOptionResponse] = Field(
        description="The roles an admin can give, with their labels, in the order to show them."
    )
    members: list[TeamMemberResponse] = Field(
        description="The team's active members, ordered by name ignoring case."
    )
