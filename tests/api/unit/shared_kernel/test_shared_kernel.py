"""The shared kernel is pure Python: it is tested without a database or a framework."""

from dataclasses import FrozenInstanceError
from datetime import UTC, datetime

import pytest

from agilina_api.shared_kernel import AggregateRoot, DomainError, DomainEvent, Entity
from tests.api.builders import next_id


class _Thing(Entity[str]):
    pass


class _OtherThing(Entity[str]):
    pass


class _Happened(DomainEvent):
    pass


class _Order(AggregateRoot[str]):
    def place(self, at: datetime) -> None:
        self._record(_Happened(occurred_at=at))


def test_entities_with_the_same_identity_are_equal():
    assert _Thing("a") == _Thing("a")
    assert hash(_Thing("a")) == hash(_Thing("a"))


def test_entities_with_different_identity_are_different():
    assert _Thing("a") != _Thing("b")


def test_entities_of_different_types_are_never_equal_even_with_the_same_identity():
    assert _Thing("a") != _OtherThing("a")


def test_an_entity_is_not_equal_to_something_that_is_not_an_entity():
    assert _Thing("a") != "a"


def test_an_entity_exposes_its_identity():
    identity = next_id()
    assert Entity(identity).id == identity


def test_an_aggregate_records_events_and_hands_them_over_only_once():
    now = datetime(2026, 10, 3, tzinfo=UTC)
    order = _Order("o-1")
    order.place(now)

    events = order.pull_events()

    assert events == [_Happened(occurred_at=now)]
    assert order.pull_events() == []


def test_a_domain_event_is_immutable():
    event = _Happened(occurred_at=datetime(2026, 10, 3, tzinfo=UTC))
    with pytest.raises(FrozenInstanceError):
        event.occurred_at = datetime(2026, 10, 4, tzinfo=UTC)  # type: ignore[misc]


def test_domain_errors_are_exceptions():
    assert issubclass(DomainError, Exception)
