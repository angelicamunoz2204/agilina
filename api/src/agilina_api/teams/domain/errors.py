"""Errors of the teams domain."""

from agilina_api.shared_kernel import DomainError


class InvalidTeamNameError(DomainError):
    """A team's name cannot be blank or longer than 80 characters once trimmed (HU-05)."""


class AlreadyMemberError(DomainError):
    """That person is already an active member of the team."""


class TeamNotFoundError(DomainError):
    """There is no team with that identifier."""


class MemberNotFoundError(DomainError):
    """That person is not an active member of the team: never was, or was removed (HU-06)."""


class LastAdminError(DomainError):
    """The change would leave the team without an admin: its only admin cannot be demoted
    or removed, not even by themselves (HU-06)."""


class RoleChangeDuringActiveSprintError(DomainError):
    """Roles do not change while the team has a sprint in progress (HU-06)."""
