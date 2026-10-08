from agilina_api.shared_kernel import DomainError


class SprintEndsBeforeStartError(DomainError):
    """A sprint's last day cannot come before its first one; both may be the same day
    (HU-07)."""
