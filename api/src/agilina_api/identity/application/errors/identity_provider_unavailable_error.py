class IdentityProviderUnavailableError(Exception):
    """The identity provider did not answer or failed. Not a business rule: it is an
    outage, and the interface reports it as such."""
