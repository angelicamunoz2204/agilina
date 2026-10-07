"""InviteToTeam: who is invited decides what happens (HU-06, acceptance criterion 2).

An email without an account gets the HU-02 invitation with its activation link; an
existing account joins the team at once and gets a notice without a link; a current member
is refused; and a pending invitation to the team stops working either way.
"""

from dataclasses import replace

import pytest

from agilina_api.identity.application.commands.invite_to_team import InviteToTeamHandler
from agilina_api.identity.application.commands.issue_invitation import IssueInvitationHandler
from agilina_api.identity.application.dtos import TeamInvitationOutcome
from agilina_api.identity.domain.errors import (
    AccountDisabledError,
    AlreadyTeamMemberError,
    InvalidEmailError,
    InvalidFullNameError,
    UnknownTeamError,
)
from agilina_api.identity.domain.invitation import InvitationStatus
from agilina_api.shared.application.ports import MailDeliveryError
from agilina_shared.enums import Language, TeamRole
from tests.api.builders import (
    TOKEN,
    AppUserBuilder,
    InvitationBuilder,
    InviteToTeamBuilder,
    TeamContactsBuilder,
    next_id,
)
from tests.api.doubles import (
    FakeClock,
    FakeIdentityUnitOfWork,
    FakeMailer,
    FakeRenderer,
    FakeTeamContactsDirectory,
    FakeTokenGenerator,
)

JULIAN = "julian@example.test"


class Scenario:
    """Diego, admin of Atlas (in Spanish), invites people to it."""

    def __init__(self) -> None:
        self.team_id = next_id()
        self.diego = AppUserBuilder().with_email("diego@example.test").named("Diego").build()
        self.membership_id = next_id()
        self.uow = FakeIdentityUnitOfWork()
        self.mailer = FakeMailer()
        self.clock = FakeClock()
        contacts = FakeTeamContactsDirectory(
            {self.team_id: TeamContactsBuilder().named("Atlas").in_language(Language.ES).build()}
        )
        issue = IssueInvitationHandler(
            self.uow.factory(),
            FakeTokenGenerator(TOKEN),
            FakeRenderer(),
            self.mailer,
            self.clock,
            "https://app.test/activate",
        )
        self.handler = InviteToTeamHandler(
            self.uow.factory(),
            contacts,
            issue,
            FakeRenderer(),
            self.mailer,
            self.clock,
            "https://app.test/teams/",
        )

    async def with_inviter(self) -> "Scenario":
        await self.uow.users.add(self.diego)
        return self

    def command(self) -> InviteToTeamBuilder:
        return (
            InviteToTeamBuilder().for_team(self.team_id).by_admin(self.diego.id, self.membership_id)
        )

    async def invite(self, builder: InviteToTeamBuilder | None = None):
        return await self.handler.handle((builder or self.command()).build())


@pytest.fixture
async def scenario() -> Scenario:
    return await Scenario().with_inviter()


# ------------------------------------------------------------ without account --
async def test_an_email_without_account_gets_an_invitation_as_member_by_default(scenario):
    outcome = await scenario.invite()

    assert outcome is TeamInvitationOutcome.INVITATION_SENT
    [invitation] = scenario.uow.invitations.by_id.values()
    assert invitation.status is InvitationStatus.PENDING
    assert invitation.team_id == scenario.team_id and invitation.email.value == JULIAN
    assert invitation.role is TeamRole.MEMBER
    assert scenario.uow.team_membership.added == [] and scenario.uow.commits == 1


async def test_the_invitation_records_the_admins_membership_as_its_author(scenario):
    await scenario.invite()

    [invitation] = scenario.uow.invitations.by_id.values()
    assert invitation.created_by == scenario.membership_id


async def test_the_chosen_role_travels_in_the_invitation(scenario):
    await scenario.invite(scenario.command().as_admin())

    [invitation] = scenario.uow.invitations.by_id.values()
    assert invitation.role is TeamRole.ADMIN


async def test_the_invitation_email_carries_the_activation_link_in_the_teams_language(scenario):
    await scenario.invite(scenario.command().named("  Julián Torres  "))

    [message] = scenario.mailer.sent
    assert message.to == JULIAN and message.subject == "invitation:es"
    assert f"activation_url=https://app.test/activate#t={TOKEN}" in message.text_body
    assert "inviter_name=Diego" in message.text_body and "team_name=Atlas" in message.text_body
    assert "name=Julián Torres," in message.text_body


async def test_an_inviter_without_account_is_left_out_of_the_email(scenario):
    stranger = InviteToTeamBuilder().for_team(scenario.team_id).by_admin(next_id(), next_id())

    await scenario.invite(stranger)

    assert "inviter_name=," in scenario.mailer.sent[0].text_body


async def test_inviting_again_revokes_the_previous_link(scenario):
    await scenario.invite()
    [first] = scenario.uow.invitations.by_id

    await scenario.invite()

    statuses = {i.id: i.status for i in scenario.uow.invitations.by_id.values()}
    assert statuses.pop(first) is InvitationStatus.REVOKED
    assert list(statuses.values()) == [InvitationStatus.PENDING]
    assert len(scenario.mailer.sent) == 2


# ---------------------------------------------------------- existing account --
async def test_an_existing_account_joins_the_team_with_the_chosen_role_without_a_token(scenario):
    julian = await AppUserBuilder().with_email(JULIAN).saved_in(scenario.uow.users)

    outcome = await scenario.invite(scenario.command().as_admin())

    assert outcome is TeamInvitationOutcome.MEMBER_ADDED
    assert scenario.uow.team_membership.added == [(scenario.team_id, julian.id, TeamRole.ADMIN)]
    assert scenario.uow.invitations.by_id == {}
    assert scenario.uow.commits == 1


async def test_the_address_is_matched_whatever_its_case(scenario):
    julian = await AppUserBuilder().with_email(JULIAN).saved_in(scenario.uow.users)

    await scenario.invite(scenario.command().with_email("  Julian@Example.TEST "))

    assert scenario.uow.team_membership.added == [(scenario.team_id, julian.id, TeamRole.MEMBER)]


async def test_an_existing_account_gets_a_notice_with_the_team_link_and_no_activation(scenario):
    await AppUserBuilder().with_email(JULIAN).named("Julián T.").saved_in(scenario.uow.users)

    await scenario.invite(scenario.command().named("Someone Else"))

    [message] = scenario.mailer.sent
    assert message.to == JULIAN and message.subject == "member_added:es"
    assert f"team_url=https://app.test/teams/{scenario.team_id}" in message.text_body
    assert "name=Julián T.," in message.text_body  # the account's name, not the form's
    assert "inviter_name=Diego" in message.text_body and "team_name=Atlas" in message.text_body
    assert "activate" not in message.text_body and "#t=" not in message.text_body


async def test_a_pending_invitation_of_an_existing_account_is_revoked(scenario):
    await AppUserBuilder().with_email(JULIAN).saved_in(scenario.uow.users)
    pending = (
        await InvitationBuilder().for_team(scenario.team_id).saved_in(scenario.uow.invitations)
    )

    await scenario.invite()

    assert scenario.uow.invitations.by_id[pending.id].status is InvitationStatus.REVOKED


async def test_an_overdue_invitation_of_an_existing_account_is_marked_expired(scenario):
    await AppUserBuilder().with_email(JULIAN).saved_in(scenario.uow.users)
    overdue = await (
        InvitationBuilder()
        .for_team(scenario.team_id)
        .past_its_deadline()
        .saved_in(scenario.uow.invitations)
    )

    await scenario.invite()

    assert scenario.uow.invitations.by_id[overdue.id].status is InvitationStatus.EXPIRED


async def test_a_current_member_is_refused_without_email_nor_commit(scenario):
    await AppUserBuilder().with_email(JULIAN).saved_in(scenario.uow.users)
    scenario.uow.team_membership.fail_with = AlreadyTeamMemberError("already in Atlas")

    with pytest.raises(AlreadyTeamMemberError):
        await scenario.invite()

    assert scenario.mailer.sent == [] and scenario.uow.commits == 0


async def test_if_the_notice_cannot_be_sent_nothing_is_committed(scenario):
    await AppUserBuilder().with_email(JULIAN).saved_in(scenario.uow.users)
    scenario.mailer.fail = True

    with pytest.raises(MailDeliveryError):
        await scenario.invite()

    assert scenario.uow.commits == 0


async def test_a_disabled_account_is_refused_and_nothing_is_done(scenario):
    await AppUserBuilder().with_email(JULIAN).disabled().saved_in(scenario.uow.users)

    with pytest.raises(AccountDisabledError):
        await scenario.invite()

    assert scenario.uow.team_membership.added == [] and scenario.uow.invitations.by_id == {}
    assert scenario.mailer.sent == [] and scenario.uow.commits == 0


# ---------------------------------------------------------------- refused --
@pytest.mark.parametrize(
    ("field", "value", "error"),
    [
        ("email", "not-an-email", InvalidEmailError),
        ("full_name", "   ", InvalidFullNameError),
        ("team_id", None, UnknownTeamError),
    ],
)
async def test_invalid_data_or_an_unknown_team_is_refused_before_anything_is_sent(
    scenario, field, value, error
):
    command = scenario.command().build()
    command = replace(command, **{field: value if value is not None else next_id()})

    with pytest.raises(error):
        await scenario.handler.handle(command)

    assert scenario.mailer.sent == [] and scenario.uow.commits == 0
    assert scenario.uow.invitations.by_id == {} and scenario.uow.team_membership.added == []
