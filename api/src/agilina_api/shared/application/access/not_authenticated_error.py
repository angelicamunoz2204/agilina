class NotAuthenticatedError(Exception):
    """The request carries no bearer token, or one that does not identify a user of
    Agilina. Not a business rule: the interface answers it with a ``401``."""
