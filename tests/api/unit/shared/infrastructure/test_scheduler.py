"""The scheduler keeps its jobs in the application's own database."""

from agilina_api.shared.infrastructure.scheduler import JOBS_TABLE, create_scheduler
from agilina_api.shared.infrastructure.settings import get_settings


def test_the_scheduler_is_created_with_a_persistent_store_and_in_utc():
    scheduler = create_scheduler(get_settings())  # nothing connects until it starts

    store = scheduler._jobstores["default"]  # noqa: SLF001 - there is no public accessor
    assert store.jobs_t.name == JOBS_TABLE
    assert str(scheduler.timezone) == "UTC"
    assert scheduler.running is False
