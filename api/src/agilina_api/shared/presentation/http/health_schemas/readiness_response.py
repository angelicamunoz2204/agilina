from agilina_api.shared.presentation.http.health_schemas.service_status_response import (
    ServiceStatusResponse,
)


class ReadinessResponse(ServiceStatusResponse):
    database: str
