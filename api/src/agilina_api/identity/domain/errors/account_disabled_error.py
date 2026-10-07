from agilina_api.shared_kernel import DomainError


class AccountDisabledError(DomainError):
    """The person invited has an account in Agilina, but it is disabled: they could not
    enter the team, so nothing is done (HU-06)."""
