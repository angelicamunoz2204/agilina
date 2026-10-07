from collections.abc import Mapping
from typing import Any

from agilina_api.shared.presentation.http.api_error.api_error import ApiError


class ApiException(Exception):  # noqa: N818 - it carries the HTTP answer, not a failure kind
    """Raised by the presentation layer when no domain error says it already.

    ``details`` is what the interface adds to the catalog entry (for example the failing
    fields); it never holds a value the caller sent.
    """

    def __init__(self, error: ApiError, details: Mapping[str, Any] | None = None) -> None:
        super().__init__(error.code)
        self.error = error
        self.details = details
