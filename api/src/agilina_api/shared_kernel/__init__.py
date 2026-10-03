"""Shared kernel: the base building blocks of every domain model.

Pure Python, no framework. Every ``domain`` package may use it; it imports
nothing from the rest of the API.
"""

from agilina_api.shared_kernel.aggregate_root import AggregateRoot
from agilina_api.shared_kernel.domain_event import DomainEvent
from agilina_api.shared_kernel.entity import Entity
from agilina_api.shared_kernel.errors import DomainError

__all__ = ["AggregateRoot", "DomainError", "DomainEvent", "Entity"]
