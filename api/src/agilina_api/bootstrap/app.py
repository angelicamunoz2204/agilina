"""API entry point and composition root.

Run: ``make api`` · Interactive documentation: http://localhost:8000/docs
"""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from agilina_api import __version__
from agilina_api.bootstrap.container import build_container
from agilina_api.ceremonies.presentation.http import router as ceremonies_router
from agilina_api.identity.presentation.http import dependencies as identity_dependencies
from agilina_api.identity.presentation.http import router as identity_router
from agilina_api.identity.presentation.http.errors import IDENTITY_ERRORS
from agilina_api.shared.application.health import GetLiveness, GetReadiness
from agilina_api.shared.infrastructure.database_probe import SqlDatabaseProbe
from agilina_api.shared.infrastructure.logging_setup import configure_logging, get_logger
from agilina_api.shared.infrastructure.scheduler import create_scheduler
from agilina_api.shared.infrastructure.settings import get_settings
from agilina_api.shared.presentation.http import health_router
from agilina_api.shared.presentation.http.access import get_authenticated_users, get_team_access
from agilina_api.shared.presentation.http.dependencies import (
    get_liveness_query,
    get_readiness_query,
)
from agilina_api.shared.presentation.http.errors import SHARED_ERRORS, register_error_handlers
from agilina_api.teams.presentation.http import dependencies as teams_dependencies
from agilina_api.teams.presentation.http import router as teams_router
from agilina_api.teams.presentation.http.errors import TEAMS_ERRORS

logger = get_logger(__name__)

DESCRIPTION = """
Source of truth of the Agilina domain.

This specification is the contract with the web application and with the agent
worker: it is generated from the types, so it cannot drift from the code.
"""


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Start the scheduler with the application and stop it with it.

    If the database is unavailable, the API stays up without a scheduler and
    logs it: a deferred job must not bring the API down.
    """
    settings = get_settings()
    configure_logging(settings.log_level)
    logger.info("Starting agilina-api %s in environment %s", __version__, settings.environment)

    scheduler = None
    try:
        scheduler = create_scheduler(settings)
        scheduler.start()
        app.state.scheduler = scheduler
        logger.info("Scheduler started")
    except Exception as error:  # running without a scheduler is degradation, not a crash
        app.state.scheduler = None
        logger.warning("The scheduler could not start: %s", error)

    yield

    await app.state.container.aclose()
    if scheduler is not None and scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("Scheduler stopped")


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="Agilina API",
        version=__version__,
        description=DESCRIPTION,
        lifespan=lifespan,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(health_router.router)
    app.include_router(ceremonies_router.router)
    app.include_router(identity_router.router)
    app.include_router(teams_router.router)
    app.include_router(identity_router.team_invitations_router)
    register_error_handlers(app, (*SHARED_ERRORS, *IDENTITY_ERRORS, *TEAMS_ERRORS))

    # Wiring: presentation declares what it needs, this is where it is provided.
    liveness = GetLiveness(__version__, settings.environment)
    readiness = GetReadiness(SqlDatabaseProbe(), __version__, settings.environment)
    container = build_container(settings)
    app.state.container = container
    app.dependency_overrides[identity_dependencies.get_invitation_status_handler] = (
        lambda: container.invitation_status
    )
    app.dependency_overrides[identity_dependencies.get_activate_account_handler] = (
        lambda: container.activate_account
    )
    app.dependency_overrides[identity_dependencies.get_request_new_invitation_handler] = (
        lambda: container.request_new_invitation
    )
    app.dependency_overrides[identity_dependencies.get_invite_to_team_handler] = (
        lambda: container.invite_to_team
    )
    app.dependency_overrides[teams_dependencies.get_create_team_as_admin_handler] = (
        lambda: container.create_team_as_admin
    )
    app.dependency_overrides[teams_dependencies.get_list_my_teams_handler] = (
        lambda: container.list_my_teams
    )
    app.dependency_overrides[teams_dependencies.get_get_team_handler] = lambda: container.get_team
    app.dependency_overrides[teams_dependencies.get_list_team_members_handler] = (
        lambda: container.list_team_members
    )
    app.dependency_overrides[teams_dependencies.get_change_member_role_handler] = (
        lambda: container.change_member_role
    )
    app.dependency_overrides[teams_dependencies.get_remove_member_handler] = (
        lambda: container.remove_member
    )
    app.dependency_overrides[get_authenticated_users] = lambda: container.authenticated_users
    app.dependency_overrides[get_team_access] = lambda: container.team_access
    app.dependency_overrides[get_liveness_query] = lambda: liveness
    app.dependency_overrides[get_readiness_query] = lambda: readiness
    return app


app = create_app()
