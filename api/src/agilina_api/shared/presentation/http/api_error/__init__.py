"""The catalog of HTTP errors: the only place that pairs a status with a ``code`` and a message.

Every failure of the API answers with the same body (see ``error_schema``). The ``code`` is
the contract: the web turns it into text in the person's language. The ``message`` is English,
for developers, and is generic on purpose: it never names people, invitations or tenants.

Each context declares its own catalog next to its mapping table; the ones every context may
use live here. ``docs/api.md`` lists which endpoint can answer which of them.
"""

from agilina_api.shared.presentation.http.api_error.api_error import ApiError
from agilina_api.shared.presentation.http.api_error.api_exception import ApiException
from agilina_api.shared.presentation.http.api_error.catalog_of import catalog_of
from agilina_api.shared.presentation.http.api_error.shared_errors import SharedErrors

__all__ = [
    "ApiError",
    "ApiException",
    "SharedErrors",
    "catalog_of",
]
