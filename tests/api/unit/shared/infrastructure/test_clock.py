"""The system clock returns timezone-aware UTC instants (AD-20)."""

from datetime import UTC, timedelta

from agilina_api.shared.infrastructure.clock import SystemClock


def test_the_system_clock_returns_an_aware_utc_instant():
    now = SystemClock().now()

    assert now.tzinfo is UTC
    assert now.utcoffset() == timedelta(0)
