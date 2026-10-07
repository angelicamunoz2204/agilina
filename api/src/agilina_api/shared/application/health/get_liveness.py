from agilina_api.shared.application.health.service_status import ServiceStatus


class GetLiveness:
    def __init__(self, version: str, environment: str) -> None:
        self._version = version
        self._environment = environment

    def handle(self) -> ServiceStatus:
        return ServiceStatus(self._version, self._environment, status="alive")
