from agilina_api.shared_kernel import DomainError


class NoDailyParticipantsError(DomainError):
    """A sprint is configured with at least one daily participant (HU-07). Removing a member
    later may still leave it with none."""
