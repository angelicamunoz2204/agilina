from dataclasses import dataclass


@dataclass(frozen=True)
class MemberContact:
    """How a member is called and reached. Identity owns it; teams asks for it by port."""

    full_name: str
    email: str
