class NotATeamAdminError(Exception):
    """The user is an active member of the team but not one of its admins, and the request
    is one only an admin may make (HU-06). Not a business rule: the interface answers it
    with a ``403``."""
