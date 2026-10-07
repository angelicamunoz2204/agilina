from agilina_api.shared_kernel import DomainError


class LastAdminError(DomainError):
    """The change would leave the team without an admin: its only admin cannot be demoted
    or removed, not even by themselves (HU-06)."""
