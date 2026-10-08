from agilina_api.shared_kernel import DomainError


class DuplicateDailyParticipantError(DomainError):
    """The same person appears more than once among the daily's participants: each one has a
    single turn (HU-07)."""
