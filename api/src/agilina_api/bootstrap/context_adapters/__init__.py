"""Adapters that connect one bounded context to another.

``identity`` cannot import ``teams`` (AD-21), so it declares what it needs as ports; the
implementations that use the teams use cases live here, in the composition root, which is
the only place allowed to know both.
"""

from agilina_api.bootstrap.context_adapters.team_membership_factory import team_membership_factory
from agilina_api.bootstrap.context_adapters.teams_backed_contacts import TeamsBackedContacts
from agilina_api.bootstrap.context_adapters.teams_backed_membership import TeamsBackedMembership

__all__ = [
    "TeamsBackedContacts",
    "TeamsBackedMembership",
    "team_membership_factory",
]
