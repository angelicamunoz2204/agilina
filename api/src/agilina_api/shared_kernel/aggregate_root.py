"""Aggregate root: the only entry point to the objects of an aggregate.

It protects the invariants of the aggregate and records the domain events its
behavior produces. Whoever persists the aggregate pulls the events afterwards
and publishes them.
"""

from agilina_api.shared_kernel.domain_event import DomainEvent
from agilina_api.shared_kernel.entity import Entity


class AggregateRoot[IdT](Entity[IdT]):
    def __init__(self, entity_id: IdT) -> None:
        super().__init__(entity_id)
        self._events: list[DomainEvent] = []

    def _record(self, event: DomainEvent) -> None:
        self._events.append(event)

    def pull_events(self) -> list[DomainEvent]:
        """Return the recorded events and forget them, so they are published once."""
        events, self._events = self._events, []
        return events
