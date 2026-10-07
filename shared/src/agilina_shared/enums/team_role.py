from enum import StrEnum


class TeamRole(StrEnum):
    """Internal roles per team. A person can be a member in one team and an
    admin in another: the role is always resolved against the team of the
    request, and a token claim is never trusted without checking the
    membership."""

    ADMIN = "admin"
    MEMBER = "member"
