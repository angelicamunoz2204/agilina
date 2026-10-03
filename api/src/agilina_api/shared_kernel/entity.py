"""Entity: an object defined by its identity, not by its attributes."""

from typing import Any


class Entity[IdT]:
    def __init__(self, entity_id: IdT) -> None:
        self._id = entity_id

    @property
    def id(self) -> IdT:
        return self._id

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Entity):
            return NotImplemented
        other_entity: Entity[Any] = other
        return type(self) is type(other_entity) and self._id == other_entity._id

    def __hash__(self) -> int:
        return hash((type(self), self._id))
