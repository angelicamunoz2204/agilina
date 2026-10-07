class TenantNotFoundError(Exception):
    """The tenant does not exist, is suspended, or its name is not even a valid slug. They all
    answer the same, a ``404``, so that nobody can tell which tenants exist."""
