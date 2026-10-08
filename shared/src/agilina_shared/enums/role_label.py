from enum import StrEnum


class RoleLabel(StrEnum):
    """How a role is shown to people. Stable codes that the interface translates.

    It is never stored and never authorizes anything: it is derived from a role and the
    team's mode by ``role_label``, and rules are evaluated against the role itself.
    """

    MEMBER = "member"
    SCRUM_MASTER = "scrum_master"
    ADMIN = "admin"
