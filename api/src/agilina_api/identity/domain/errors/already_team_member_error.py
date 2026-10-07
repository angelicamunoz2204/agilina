from agilina_api.shared_kernel import DomainError


class AlreadyTeamMemberError(DomainError):
    """The person invited is already an active member of that team (HU-06)."""
