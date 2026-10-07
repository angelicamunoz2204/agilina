from typing import Any

from agilina_api.shared.presentation.http.api_error import ApiError
from agilina_api.shared.presentation.http.error_schema.error_envelope import ErrorEnvelope


def errors_of(*errors: ApiError) -> dict[int | str, dict[str, Any]]:
    """The ``responses=`` of an endpoint: one entry per status, listing its codes."""
    by_status: dict[int, list[ApiError]] = {}
    for error in errors:
        by_status.setdefault(error.status, []).append(error)
    return {
        status: {
            "model": ErrorEnvelope,
            "description": " · ".join(f"`{e.code}`: {e.message}" for e in group),
        }
        for status, group in by_status.items()
    }
