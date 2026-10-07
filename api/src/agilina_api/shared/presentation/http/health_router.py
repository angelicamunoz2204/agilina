"""Health probes: ``/health`` (alive) and ``/health/ready`` (can serve)."""

from fastapi import APIRouter, Depends, Response, status

from agilina_api.shared.application.health import GetLiveness, GetReadiness
from agilina_api.shared.presentation.http.dependencies import (
    get_liveness_query,
    get_readiness_query,
)
from agilina_api.shared.presentation.http.health_schemas import (
    ReadinessResponse,
    ServiceStatusResponse,
)

router = APIRouter(tags=["health"])


@router.get("/health", response_model=ServiceStatusResponse, summary="Liveness probe")
async def health(query: GetLiveness = Depends(get_liveness_query)) -> ServiceStatusResponse:
    result = query.handle()
    return ServiceStatusResponse(
        version=result.version, environment=result.environment, status=result.status
    )


@router.get(
    "/health/ready",
    response_model=ReadinessResponse,
    summary="Readiness probe",
    responses={503: {"description": "Some dependency is not responding"}},
)
async def ready(
    response: Response, query: GetReadiness = Depends(get_readiness_query)
) -> ReadinessResponse:
    result = await query.handle()
    if result.status != "ready":
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    return ReadinessResponse(
        version=result.version,
        environment=result.environment,
        status=result.status,
        database=result.database,
    )
