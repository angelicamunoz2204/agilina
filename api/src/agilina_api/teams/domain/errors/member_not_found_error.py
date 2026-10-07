from agilina_api.shared_kernel import DomainError


class MemberNotFoundError(DomainError):
    """That person is not an active member of the team: never was, or was removed (HU-06)."""
