"""The body of every error response, as the OpenAPI document shows it."""

from agilina_api.shared.presentation.http.error_schema.error_body import ErrorBody
from agilina_api.shared.presentation.http.error_schema.error_envelope import ErrorEnvelope
from agilina_api.shared.presentation.http.error_schema.errors_of import errors_of

__all__ = [
    "ErrorBody",
    "ErrorEnvelope",
    "errors_of",
]
