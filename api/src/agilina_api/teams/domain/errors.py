"""Errors of the teams domain."""

from agilina_api.shared_kernel import DomainError


class InvalidTeamNameError(DomainError):
    """A team's name cannot be blank (HU-05)."""


class AlreadyMemberError(DomainError):
    """That person is already an active member of the team."""


class TeamNotFoundError(DomainError):
    """There is no team with that identifier."""
