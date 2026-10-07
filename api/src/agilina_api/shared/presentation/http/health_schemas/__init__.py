"""Response models of the health probes."""

from agilina_api.shared.presentation.http.health_schemas.readiness_response import (
    ReadinessResponse,
)
from agilina_api.shared.presentation.http.health_schemas.service_status_response import (
    ServiceStatusResponse,
)

__all__ = ["ReadinessResponse", "ServiceStatusResponse"]
