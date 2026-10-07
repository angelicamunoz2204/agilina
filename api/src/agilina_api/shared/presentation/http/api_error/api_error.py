from collections.abc import Mapping
from dataclasses import dataclass


@dataclass(frozen=True)
class ApiError:
    status: int
    code: str
    message: str
    headers: Mapping[str, str] | None = None
