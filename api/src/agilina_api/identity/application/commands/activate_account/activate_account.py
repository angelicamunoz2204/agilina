from dataclasses import dataclass, field


@dataclass(frozen=True)
class ActivateAccount:
    token: str
    password: str = field(repr=False)
