"""One logging configuration for the whole application."""

import logging

from agilina_api.shared.infrastructure.logging_setup import configure_logging, get_logger


def test_the_level_is_applied_whatever_its_case(untouched_logging):
    configure_logging("debug")

    assert logging.getLogger().level == logging.DEBUG


def test_uvicorn_access_logs_are_not_duplicated(untouched_logging):
    configure_logging()

    assert logging.getLogger("uvicorn.access").propagate is False


def test_a_logger_carries_the_name_it_is_asked_for():
    assert get_logger("agilina.something").name == "agilina.something"
