from agilina_api.shared_kernel import DomainError


class AlreadyMemberError(DomainError):
    """That person is already an active member of the team."""
