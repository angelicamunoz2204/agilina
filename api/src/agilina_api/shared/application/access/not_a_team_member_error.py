class NotATeamMemberError(Exception):
    """The user is not an active member of the team the request is about. The team may
    not even exist: both answer the same so that nobody can find out which teams exist.
    Not a business rule: the interface answers it with a ``403``."""
