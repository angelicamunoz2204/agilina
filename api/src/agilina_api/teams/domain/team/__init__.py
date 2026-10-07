"""The ``Team`` aggregate: a team, its configuration and its members.

The team is the tenant of the whole product. Membership lives inside the aggregate
because the rules that matter (nobody joins twice, a team keeps at least one admin) are
about the team as a whole. The label shown for a role is *not* stored: it is derived from
the role and the team's mode in the presentation layer (HU-04).
"""

from agilina_api.teams.domain.team.membership import Membership
from agilina_api.teams.domain.team.membership_status import MembershipStatus
from agilina_api.teams.domain.team.team import Team

__all__ = [
    "Membership",
    "MembershipStatus",
    "Team",
]
