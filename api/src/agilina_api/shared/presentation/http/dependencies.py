"""Dependency providers declared by the shared presentation layer.

The composition root overrides them with the real wiring, so this layer never
imports the infrastructure one.
"""

from agilina_api.shared.application.health import GetLiveness, GetReadiness


def get_liveness_query() -> GetLiveness:
    raise NotImplementedError("Wired by the composition root")


def get_readiness_query() -> GetReadiness:
    raise NotImplementedError("Wired by the composition root")
