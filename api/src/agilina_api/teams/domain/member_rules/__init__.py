"""What can block changing a member's role or removing them from the team (HU-06).

Pure functions, so the ``Team`` aggregate (which enforces the rules) and the members list
(which tells the interface why a control is disabled) answer from the same source and
the interface never computes a rule.
"""

from agilina_api.teams.domain.member_rules.is_last_admin import is_last_admin
from agilina_api.teams.domain.member_rules.member_change_blocker import MemberChangeBlocker
from agilina_api.teams.domain.member_rules.removal_blocker import removal_blocker
from agilina_api.teams.domain.member_rules.role_change_blocker import role_change_blocker

__all__ = [
    "MemberChangeBlocker",
    "is_last_admin",
    "removal_blocker",
    "role_change_blocker",
]
