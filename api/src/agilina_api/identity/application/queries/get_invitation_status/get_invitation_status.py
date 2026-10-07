from dataclasses import dataclass


@dataclass(frozen=True)
class GetInvitationStatus:
    token: str
