from typing import Any

from agilina_api.shared.presentation.http.api_error import ApiError, SharedErrors
from agilina_api.shared.presentation.http.error_schema.error_envelope import ErrorEnvelope


def errors_of(*errors: ApiError) -> dict[int | str, dict[str, Any]]:
    """The ``responses=`` of an endpoint: one entry per status, listing its codes.

    Every endpoint can answer ``500 internal_error`` (a failure nobody planned for), so it is
    always listed, whether the caller names it or not.
    """
    by_status: dict[int, list[ApiError]] = {}
    for error in (*errors, SharedErrors.INTERNAL):
        if error in by_status.get(error.status, []):
            continue
        by_status.setdefault(error.status, []).append(error)
    return {
        status: {
            "model": ErrorEnvelope,
            "description": " · ".join(f"`{e.code}`: {e.message}" for e in group),
        }
        for status, group in by_status.items()
    }
