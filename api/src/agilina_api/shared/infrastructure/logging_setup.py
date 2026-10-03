"""Event logging.

The minimum observability the architecture asks for is a scheduler log and a
record of every adapter call with its result. It starts with a single
configuration so every module writes the same way from the first commit.
"""

import logging
import sys


def configure_logging(level: str = "INFO") -> None:
    log_format = "%(asctime)s %(levelname)-8s %(name)s · %(message)s"
    logging.basicConfig(
        level=level.upper(),
        format=log_format,
        datefmt="%Y-%m-%dT%H:%M:%S%z",
        stream=sys.stdout,
        force=True,
    )
    # Uvicorn duplicates access logs with its own format; only one is kept.
    logging.getLogger("uvicorn.access").propagate = False


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
