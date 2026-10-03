"""Base of every domain error.

A domain rule that is broken raises a subclass of ``DomainError`` (for example
``InvitationExpiredError``). One handler in the presentation layer translates
them to HTTP responses; the domain knows nothing about status codes.
"""


class DomainError(Exception):
    """A business rule was violated."""
