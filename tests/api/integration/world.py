"""The scenario the integration tests of the identity use cases share: real database and
real repositories; Keycloak, the mailer and the clock are doubles."""

from dataclasses import replace

from agilina_api.bootstrap.context_adapters import TeamsBackedContacts, team_membership_factory
from agilina_api.identity.application.commands.activate_account import ActivateAccountHandler
from agilina_api.identity.application.commands.issue_invitation import IssueInvitationHandler
from agilina_api.identity.application.commands.request_new_invitation import (
    RequestNewInvitationHandler,
)
from agilina_api.identity.application.queries.get_invitation_status import (
    GetInvitationStatusHandler,
)
from agilina_api.identity.infrastructure.persistence.invitation_queries import SqlInvitationQueries
from agilina_api.identity.infrastructure.persistence.unit_of_work import (
    identity_unit_of_work_factory,
)
from agilina_api.identity.infrastructure.persistence.user_contacts import SqlUserContacts
from agilina_api.teams.application.commands.create_team import CreateTeam, CreateTeamHandler
from agilina_api.teams.infrastructure.persistence.team_queries import SqlTeamQueries
from agilina_api.teams.infrastructure.persistence.unit_of_work import teams_unit_of_work_factory
from agilina_shared.enums import Language, TeamRole
from tests.api.builders import PASSWORD, IssueInvitationBuilder
from tests.api.doubles import (
    FakeClock,
    FakeIdentityProvider,
    FakeMailer,
    FakeRenderer,
    FakeTokenGenerator,
)

TOKENS = [letter * 43 for letter in "ABCDEFGH"]  # one per invitation: token_hash is unique
TOKEN = TOKENS[0]
__all__ = ["PASSWORD", "TOKEN", "TOKENS", "World"]


class World:
    """Real database and real repositories; Keycloak, the mailer and the clock are doubles."""

    def __init__(self, session_factory):
        self.clock = FakeClock()
        self.provider = FakeIdentityProvider()
        self.mailer = FakeMailer()
        self.team_queries = SqlTeamQueries(session_factory)
        uow = identity_unit_of_work_factory(session_factory, team_membership_factory(self.clock))
        self.create_team = CreateTeamHandler(
            teams_unit_of_work_factory(session_factory), self.clock
        )
        self.issue = IssueInvitationHandler(
            uow,
            FakeTokenGenerator(*TOKENS),
            FakeRenderer(),
            self.mailer,
            self.clock,
            "https://app.test/activar",
        )
        self.activate = ActivateAccountHandler(uow, self.provider, self.clock)
        self.status = GetInvitationStatusHandler(SqlInvitationQueries(session_factory), self.clock)
        self.request_new = RequestNewInvitationHandler(
            uow,
            TeamsBackedContacts(self.team_queries, SqlUserContacts(session_factory)),
            FakeRenderer(),
            self.mailer,
            self.clock,
        )

    async def a_team(self, name="Atlas", language=Language.ES):
        return await self.create_team.handle(CreateTeam(name=name, language=language))

    async def invite(self, team_id, email="julian@example.test", role=TeamRole.ADMIN, **extra):
        builder = IssueInvitationBuilder().for_team(team_id).with_email(email)
        builder = builder.as_admin() if role is TeamRole.ADMIN else builder
        return await self.issue.handle(replace(builder.build(), **extra))
