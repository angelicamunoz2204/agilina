"""Health queries.

``alive`` says whether the process is up and ``ready`` whether it can also
serve: the difference between restarting the container and waiting for the
database to come back.
"""

from dataclasses import dataclass
from typing import Protocol


class DatabaseProbe(Protocol):
    async def is_available(self) -> bool: ...


@dataclass(frozen=True)
class ServiceStatus:
    version: str
    environment: str
    status: str


@dataclass(frozen=True)
class ReadinessStatus(ServiceStatus):
    database: str


class GetLiveness:
    def __init__(self, version: str, environment: str) -> None:
        self._version = version
        self._environment = environment

    def handle(self) -> ServiceStatus:
        return ServiceStatus(self._version, self._environment, status="alive")


class GetReadiness:
    def __init__(self, probe: DatabaseProbe, version: str, environment: str) -> None:
        self._probe = probe
        self._version = version
        self._environment = environment

    async def handle(self) -> ReadinessStatus:
        available = await self._probe.is_available()
        return ReadinessStatus(
            self._version,
            self._environment,
            status="ready" if available else "not_ready",
            database="available" if available else "unavailable",
        )
