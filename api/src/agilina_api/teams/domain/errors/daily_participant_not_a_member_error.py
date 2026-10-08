from agilina_api.shared_kernel import DomainError


class DailyParticipantNotAMemberError(DomainError):
    """A daily participant is not an active member of the team: never was, or was removed
    (HU-07)."""
