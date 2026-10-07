"""The identifier of the request being served, for whoever logs while serving it."""

from contextvars import ContextVar

request_id_var: ContextVar[str | None] = ContextVar("request_id", default=None)
