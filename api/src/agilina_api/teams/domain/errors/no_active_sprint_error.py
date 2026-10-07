from agilina_api.shared_kernel import DomainError


class NoActiveSprintError(DomainError):
    """The team has no sprint with status ``active`` to change (HU-07)."""
