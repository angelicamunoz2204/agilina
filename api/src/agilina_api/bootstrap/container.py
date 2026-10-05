"""The composition root's object graph: every use case wired to its real adapters.

The API (``bootstrap.app``) and the operator commands (``make invite``) build the same
graph, so they cannot drift apart.
"""

from dataclasses import dataclass

from agilina_api.bootstrap.context_adapters import TeamsBackedContacts, team_membership_factory
from agilina_api.identity.application.commands.activate_account import ActivateAccountHandler
from agilina_api.identity.application.commands.issue_invitation import IssueInvitationHandler
from agilina_api.identity.application.commands.request_new_invitation import (
    RequestNewInvitationHandler,
)
from agilina_api.identity.application.queries.get_invitation_status import (
    GetInvitationStatusHandler,
)
from agilina_api.identity.infrastructure.keycloak.identity_provider import KeycloakIdentityProvider
from agilina_api.identity.infrastructure.persistence.invitation_queries import SqlInvitationQueries
from agilina_api.identity.infrastructure.persistence.unit_of_work import (
    identity_unit_of_work_factory,
)
from agilina_api.identity.infrastructure.persistence.user_contacts import SqlUserContacts
from agilina_api.identity.infrastructure.tokens import SecretsActivationTokenGenerator
from agilina_api.shared.infrastructure.clock import SystemClock
from agilina_api.shared.infrastructure.database.session import get_session_factory
from agilina_api.shared.infrastructure.mail.renderer import JinjaEmailRenderer
from agilina_api.shared.infrastructure.mail.smtp_mailer import SmtpMailer
from agilina_api.shared.infrastructure.settings import Settings
from agilina_api.teams.application.commands.create_team import CreateTeamHandler
from agilina_api.teams.application.ports.outbound import TeamQueries
from agilina_api.teams.infrastructure.persistence.team_queries import SqlTeamQueries
from agilina_api.teams.infrastructure.persistence.unit_of_work import teams_unit_of_work_factory


@dataclass
class Container:
    invitation_status: GetInvitationStatusHandler
    activate_account: ActivateAccountHandler
    request_new_invitation: RequestNewInvitationHandler
    issue_invitation: IssueInvitationHandler
    create_team: CreateTeamHandler
    team_queries: TeamQueries
    identity_provider: KeycloakIdentityProvider

    async def aclose(self) -> None:
        await self.identity_provider.aclose()


def build_container(settings: Settings) -> Container:
    """Nothing here connects to anything: sessions, HTTP clients and SMTP are used lazily,
    so building it needs neither PostgreSQL nor Keycloak."""
    clock = SystemClock()
    session_factory = get_session_factory()
    renderer = JinjaEmailRenderer()
    mailer = SmtpMailer(
        host=settings.smtp_host,
        port=settings.smtp_port,
        sender=settings.mail_from,
        username=settings.smtp_user,
        password=settings.smtp_password.get_secret_value(),
        security=settings.smtp_security,
    )
    identity_provider = KeycloakIdentityProvider(
        base_url=settings.keycloak_url,
        realm=settings.keycloak_realm,
        client_id=settings.keycloak_api_client,
        client_secret=settings.keycloak_api_secret.get_secret_value(),
    )
    identity_uow = identity_unit_of_work_factory(session_factory, team_membership_factory(clock))
    team_queries = SqlTeamQueries(session_factory)
    activation_url = f"{settings.web_public_url.rstrip('/')}/activar"

    return Container(
        invitation_status=GetInvitationStatusHandler(SqlInvitationQueries(session_factory), clock),
        activate_account=ActivateAccountHandler(identity_uow, identity_provider, clock),
        request_new_invitation=RequestNewInvitationHandler(
            identity_uow,
            TeamsBackedContacts(team_queries, SqlUserContacts(session_factory)),
            renderer,
            mailer,
            clock,
        ),
        issue_invitation=IssueInvitationHandler(
            identity_uow, SecretsActivationTokenGenerator(), renderer, mailer, clock, activation_url
        ),
        create_team=CreateTeamHandler(teams_unit_of_work_factory(session_factory), clock),
        team_queries=team_queries,
        identity_provider=identity_provider,
    )
