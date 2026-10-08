from agilina_api.shared_kernel import DomainError


class InvalidTimeZoneError(DomainError):
    """The daily's capture time zone is not an IANA time zone this system knows (HU-07,
    AD-31)."""
