from enum import StrEnum


class SprintPhase(StrEnum):
    """Where an instant falls relative to the sprint period.

    It is computed from the dates and the current instant, never stored, and it is not the
    stored ``SprintStatus`` (``planned``, ``active``, ``closed``): an active sprint can still be
    ``not_started`` or already ``finished`` until someone closes it.
    """

    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    FINISHED = "finished"
