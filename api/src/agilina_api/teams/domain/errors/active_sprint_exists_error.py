from agilina_api.shared_kernel import DomainError


class ActiveSprintExistsError(DomainError):
    """The team already has an active sprint: a team has at most one at a time, and the
    active one is edited, not started again (HU-07)."""
