from enum import StrEnum


class OperationMode(StrEnum):
    """The only difference between the two modes is whether Agilina asks for
    approval before executing an action."""

    SUPPORT = "support"
    AUTONOMOUS = "autonomous"
