"""The composition root's object graph: every use case wired to its real adapters.

The API (``bootstrap.app``) and the operator commands (``make invite``) build the same
graph, so they cannot drift apart.
"""

from dataclasses import dataclass

from agilina_api.bootstrap.authentication import ClosedAuthenticatedUsers
from agilina_api.bootstrap.context_adapters import (
    IdentityBackedMemberContacts,
    TeamsBackedContacts,
    team_membership_factory,
)
from agilina_api.identity.application.commands.activate_account import ActivateAccountHandler
from agilina_api.identity.application.commands.invite_to_team import InviteToTeamHandler
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
from agilina_api.shared.application.access import AuthenticatedUsers, TeamAccess
from agilina_api.shared.infrastructure.clock import SystemClock
from agilina_api.shared.infrastructure.database.session import get_session_factory
from agilina_api.shared.infrastructure.mail.renderer import JinjaEmailRenderer
from agilina_api.shared.infrastructure.mail.smtp_mailer import SmtpMailer
from agilina_api.shared.infrastructure.settings import Settings
from agilina_api.teams.application.commands.change_member_role import ChangeMemberRoleHandler
from agilina_api.teams.application.commands.create_team import CreateTeamHandler
from agilina_api.teams.application.commands.create_team_as_admin import CreateTeamAsAdminHandler
from agilina_api.teams.application.commands.remove_member import RemoveMemberHandler
from agilina_api.teams.application.ports.outbound import TeamQueries
from agilina_api.teams.application.queries.get_team import GetTeamHandler
from agilina_api.teams.application.queries.list_my_teams import ListMyTeamsHandler
from agilina_api.teams.application.queries.list_team_members import ListTeamMembersHandler
from agilina_api.teams.infrastructure.persistence.team_queries import SqlTeamQueries
from agilina_api.teams.infrastructure.persistence.unit_of_work import teams_unit_of_work_factory


@dataclass
class Container:
    invitation_status: GetInvitationStatusHandler
    activate_account: ActivateAccountHandler
    request_new_invitation: RequestNewInvitationHandler
    issue_invitation: IssueInvitationHandler
    invite_to_team: InviteToTeamHandler
    create_team: CreateTeamHandler
    create_team_as_admin: CreateTeamAsAdminHandler
    list_my_teams: ListMyTeamsHandler
    get_team: GetTeamHandler
    list_team_members: ListTeamMembersHandler
    change_member_role: ChangeMemberRoleHandler
    remove_member: RemoveMemberHandler
    team_queries: TeamQueries
    authenticated_users: AuthenticatedUsers
    team_access: TeamAccess
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
    teams_uow = teams_unit_of_work_factory(session_factory)
    team_queries = SqlTeamQueries(session_factory)
    user_contacts = SqlUserContacts(session_factory)
    team_contacts = TeamsBackedContacts(team_queries, user_contacts)
    web_url = settings.web_public_url.rstrip("/")
    issue_invitation = IssueInvitationHandler(
        identity_uow,
        SecretsActivationTokenGenerator(),
        renderer,
        mailer,
        clock,
        f"{web_url}/activate",
    )

    return Container(
        invitation_status=GetInvitationStatusHandler(SqlInvitationQueries(session_factory), clock),
        activate_account=ActivateAccountHandler(identity_uow, identity_provider, clock),
        request_new_invitation=RequestNewInvitationHandler(
            identity_uow, team_contacts, renderer, mailer, clock
        ),
        issue_invitation=issue_invitation,
        invite_to_team=InviteToTeamHandler(
            identity_uow,
            team_contacts,
            issue_invitation,
            renderer,
            mailer,
            clock,
            # The notice to an existing account links to the team, never to an activation.
            f"{web_url}/teams",
        ),
        create_team=CreateTeamHandler(teams_uow, clock),
        create_team_as_admin=CreateTeamAsAdminHandler(teams_uow, clock),
        list_my_teams=ListMyTeamsHandler(team_queries),
        get_team=GetTeamHandler(team_queries),
        list_team_members=ListTeamMembersHandler(
            team_queries, IdentityBackedMemberContacts(user_contacts)
        ),
        change_member_role=ChangeMemberRoleHandler(teams_uow, clock),
        remove_member=RemoveMemberHandler(teams_uow, clock),
        team_queries=team_queries,
        # TODO(HU-03): the adapter that validates Keycloak access tokens.
        authenticated_users=ClosedAuthenticatedUsers(),
        # The teams query answers the shared port as it is: the membership is checked
        # against the stored role, never against a claim of the token.
        team_access=team_queries,
        identity_provider=identity_provider,
    )
