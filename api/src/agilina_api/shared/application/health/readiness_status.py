from dataclasses import dataclass

from agilina_api.shared.application.health.service_status import ServiceStatus


@dataclass(frozen=True)
class ReadinessStatus(ServiceStatus):
    database: str
