from agilina_api.shared_kernel import DomainError


class RoleChangeDuringActiveSprintError(DomainError):
    """Roles do not change while the team has a sprint in progress (HU-06)."""
