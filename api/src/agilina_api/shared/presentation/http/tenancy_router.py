"""The tenant, as the platform knows it (AD-29).

The web asks it before anything else, to tell an address that names a real organization from
one that does not: it answers with the tenant's public data, or with the same ``404`` as any
other route when the tenant is not there. It needs the tenant header and nothing else: it is
asked before the person has signed in.
"""

from fastapi import APIRouter, Depends, Response
from pydantic import BaseModel

from agilina_api.shared.application.tenancy import Tenant
from agilina_api.shared.presentation.http.api_error import SharedErrors
from agilina_api.shared.presentation.http.error_schema import errors_of
from agilina_api.shared.presentation.http.tenancy import current_tenant
from agilina_shared.enums import Language

router = APIRouter(prefix="/v1/tenant", tags=["tenant"])


class TenantResponse(BaseModel):
    slug: str
    display_name: str
    language: Language
    """The language the tenant shows before a team has chosen its own."""


@router.get(
    "",
    response_model=TenantResponse,
    summary="The tenant the request names, if it exists and is active",
    # The 422 is the one FastAPI derives from the header parameter; the header is optional, so
    # it does not happen in practice, but it is declared in the common body.
    responses=errors_of(
        SharedErrors.TENANT_REQUIRED, SharedErrors.TENANT_NOT_FOUND, SharedErrors.VALIDATION
    ),
)
async def get_tenant(
    response: Response, tenant: Tenant = Depends(current_tenant)
) -> TenantResponse:
    response.headers["Cache-Control"] = "no-store"
    return TenantResponse(
        slug=tenant.slug, display_name=tenant.display_name, language=tenant.language
    )
