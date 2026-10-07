"""Event logging.

The minimum observability the architecture asks for is a scheduler log and a
record of every adapter call with its result. It starts with a single
configuration so every module writes the same way from the first commit.
"""

import logging
import sys

from agilina_api.shared.application.request_context import request_id_var


class RequestIdFilter(logging.Filter):
    """Adds ``request_id`` to every record so the log format can print it."""

    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = request_id_var.get() or "-"
        return True


def configure_logging(level: str = "INFO") -> None:
    log_format = "%(asctime)s %(levelname)-8s %(name)s [%(request_id)s] · %(message)s"
    logging.basicConfig(
        level=level.upper(),
        format=log_format,
        datefmt="%Y-%m-%dT%H:%M:%S%z",
        stream=sys.stdout,
        force=True,
    )
    for handler in logging.getLogger().handlers:
        handler.addFilter(RequestIdFilter())
    # Uvicorn duplicates access logs with its own format; only one is kept.
    logging.getLogger("uvicorn.access").propagate = False


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
