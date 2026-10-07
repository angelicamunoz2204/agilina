from dataclasses import dataclass


@dataclass(frozen=True)
class ServiceStatus:
    version: str
    environment: str
    status: str
