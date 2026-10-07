class TenantRequiredError(Exception):
    """The request names no tenant. Not a business rule: the interface answers a ``400``."""
