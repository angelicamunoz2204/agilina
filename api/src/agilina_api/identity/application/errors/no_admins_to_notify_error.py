from agilina_api.shared_kernel import DomainError


class NoAdminsToNotifyError(DomainError):
    """The team has nobody to tell that a new invitation was requested."""
