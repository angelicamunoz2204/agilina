"""The ``Team`` aggregate: a team, its configuration and its members.

The team is the tenant of the whole product. Membership lives inside the aggregate
because the rules that matter (nobody joins twice, a team keeps at least one admin) are
about the team as a whole. The label shown for a role is *not* stored: today the members
list (``ListTeamMembers``) repeats the role's code, and HU-04 replaces that with the label
derived from the role and the team's mode.
"""

from agilina_api.teams.domain.team.membership import Membership
from agilina_api.teams.domain.team.membership_status import MembershipStatus
from agilina_api.teams.domain.team.team import Team

__all__ = [
    "Membership",
    "MembershipStatus",
    "Team",
]
