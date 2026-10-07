from agilina_api.shared.application.health.database_probe import DatabaseProbe
from agilina_api.shared.application.health.readiness_status import ReadinessStatus


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
