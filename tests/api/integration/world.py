"""The scenario the integration tests of the identity use cases share: real database and
real repositories; Keycloak, the mailer and the clock are doubles. It also has the HU-06
use cases that manage a team's members, which cross identity and teams."""

from dataclasses import replace

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
from agilina_api.identity.infrastructure.persistence.invitation_queries import SqlInvitationQueries
from agilina_api.identity.infrastructure.persistence.unit_of_work import (
    identity_unit_of_work_factory,
)
from agilina_api.identity.infrastructure.persistence.user_contacts import SqlUserContacts
from agilina_api.shared.application.ports import EmailRenderer
from agilina_api.teams.application.commands.change_member_role import ChangeMemberRoleHandler
from agilina_api.teams.application.commands.create_team import CreateTeam, CreateTeamHandler
from agilina_api.teams.application.commands.remove_member import RemoveMemberHandler
from agilina_api.teams.application.queries.list_team_members import ListTeamMembersHandler
from agilina_api.teams.infrastructure.persistence.team_queries import SqlTeamQueries
from agilina_api.teams.infrastructure.persistence.unit_of_work import teams_unit_of_work_factory
from agilina_shared.enums import Language, TeamRole
from tests.api.builders import PASSWORD, InviteToTeamBuilder, IssueInvitationBuilder
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

    def __init__(self, session_factory, renderer: EmailRenderer | None = None):
        """``renderer`` writes the emails: ``FakeRenderer`` (template and parameters) unless
        a test needs the real ``JinjaEmailRenderer`` to read what the person receives."""
        renderer = renderer or FakeRenderer()
        self.clock = FakeClock()
        self.provider = FakeIdentityProvider()
        self.mailer = FakeMailer()
        self.team_queries = SqlTeamQueries(session_factory)
        user_contacts = SqlUserContacts(session_factory)
        team_contacts = TeamsBackedContacts(self.team_queries, user_contacts)
        uow = identity_unit_of_work_factory(session_factory, team_membership_factory(self.clock))
        teams_uow = teams_unit_of_work_factory(session_factory)
        self.create_team = CreateTeamHandler(teams_uow, self.clock)
        self.issue = IssueInvitationHandler(
            uow,
            FakeTokenGenerator(*TOKENS),
            renderer,
            self.mailer,
            self.clock,
            "https://app.test/activate",
        )
        self.activate = ActivateAccountHandler(uow, self.provider, self.clock)
        self.status = GetInvitationStatusHandler(SqlInvitationQueries(session_factory), self.clock)
        self.request_new = RequestNewInvitationHandler(
            uow, team_contacts, renderer, self.mailer, self.clock
        )
        self.invite_to_team = InviteToTeamHandler(
            uow,
            team_contacts,
            self.issue,
            renderer,
            self.mailer,
            self.clock,
            "https://app.test/teams",
        )
        self.list_members = ListTeamMembersHandler(
            self.team_queries, IdentityBackedMemberContacts(user_contacts)
        )
        self.change_role = ChangeMemberRoleHandler(teams_uow, self.clock)
        self.remove = RemoveMemberHandler(teams_uow, self.clock)

    async def a_team(self, name="Atlas", language=Language.ES):
        return await self.create_team.handle(CreateTeam(name=name, language=language))

    async def invite(self, team_id, email="julian@example.test", role=TeamRole.ADMIN, **extra):
        builder = IssueInvitationBuilder().for_team(team_id).with_email(email)
        builder = builder.as_admin() if role is TeamRole.ADMIN else builder
        return await self.issue.handle(replace(builder.build(), **extra))

    async def admin_invites(
        self,
        team_id,
        admin_id,
        email="julian@example.test",
        role=TeamRole.MEMBER,
        full_name="Julián Torres",
    ):
        """``admin_id``, an active admin of the team, invites ``email`` with ``role``, as
        the route does: the invitation's author is the admin's membership."""
        membership = await self.team_queries.membership_of(team_id=team_id, user_id=admin_id)
        if membership is None:
            raise LookupError(f"User {admin_id} is not a member of team {team_id}")
        builder = (
            InviteToTeamBuilder()
            .for_team(team_id)
            .by_admin(admin_id, membership.membership_id)
            .with_email(email)
            .named(full_name)
        )
        return await self.invite_to_team.handle(replace(builder.build(), role=role))
