"""Dependency providers declared by the presentation layer.

The composition root (``main.py``) overrides them with the real wiring, so
this layer never imports the infrastructure one.
"""

from agilina_stt.application.ports import ServiceInfo, Transcriber


def get_transcriber() -> Transcriber:
    raise NotImplementedError("Wired by the composition root")


def get_service_info() -> ServiceInfo:
    raise NotImplementedError("Wired by the composition root")
