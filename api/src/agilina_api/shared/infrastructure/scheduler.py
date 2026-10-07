"""Background job scheduler.

Agilina needs fixed-time triggers (reminder before the daily, morning
reminder, retention cleanup) and the deferred Slack reply, which requires
answering in under three seconds and doing the work afterwards. That is a
scheduler, not a broker: the guarantee needed is surviving a restart, not
distributing load (AD-08).

The store lives in the same database as the domain, so a restart does not lose
jobs. It runs inside the API process with a declared single replica; if the
deployment grew, the persisted store allows adding per-job locking.
"""

from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from agilina_api.shared.infrastructure.logging_setup import get_logger
from agilina_api.shared.infrastructure.settings import Settings

logger = get_logger(__name__)

JOBS_TABLE = "scheduled_jobs"


def create_scheduler(settings: Settings) -> AsyncIOScheduler:
    """Build the scheduler with its store in the platform's database.

    One scheduler serves every tenant (AD-29): the jobs live in the catalog, and each carries
    the tenant it is for in its arguments.

    The same connection string works as is: ``psycopg`` is synchronous for
    classic SQLAlchemy, which is what APScheduler 3 knows how to use, and
    asynchronous for the API engine.
    """
    store = SQLAlchemyJobStore(url=settings.platform_dsn, tablename=JOBS_TABLE)
    scheduler = AsyncIOScheduler(
        jobstores={"default": store},
        timezone="UTC",  # Everything is stored and operated in UTC; the zone is the browser's.
    )
    logger.info("Scheduler created with its store in %s", JOBS_TABLE)
    return scheduler
