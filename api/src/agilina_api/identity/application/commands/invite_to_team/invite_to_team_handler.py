import logging
from collections.abc import Callable

from agilina_api.identity.application.commands.invite_to_team.invite_to_team import InviteToTeam
from agilina_api.identity.application.commands.issue_invitation import (
    IssueInvitation,
    IssueInvitationHandler,
)
from agilina_api.identity.application.commands.release_pending_invitation import (
    release_pending_invitation,
)
from agilina_api.identity.application.dtos import TeamContacts, TeamInvitationOutcome
from agilina_api.identity.application.ports.outbound import (
    IdentityUnitOfWork,
    TeamContactsDirectory,
)
from agilina_api.identity.domain.errors import (
    AccountDisabledError,
    InvalidFullNameError,
    UnknownTeamError,
)
from agilina_api.identity.domain.user import AppUser
from agilina_api.identity.domain.value_objects import Email
from agilina_api.shared.application.ports import Clock, EmailMessage, EmailRenderer, Mailer

logger = logging.getLogger(__name__)


class InviteToTeamHandler:
    """Who is invited decides what happens:

    - an email without an account gets an invitation with its activation link, through the
      same ``IssueInvitation`` of HU-02 (seven days, single use, the role travels in it);
    - an existing account joins the team right away with the chosen role and gets a notice
      without any link; a pending invitation of theirs to the team is closed;
    - someone who is already an active member is refused, and nothing is stored or sent.

    Either way a pending invitation of that email to the team stops working. It does not
    check who asks: the route lets only the team's admins get here.

    ``teams_url`` is where the web shows the teams of the tenant (``…/<tenant>/teams``): the
    notice to an existing account links to ``<teams_url>/<team id>``, never to an activation.
    """

    def __init__(  # noqa: PLR0913
        self,
        uow_factory: Callable[[], IdentityUnitOfWork],
        teams: TeamContactsDirectory,
        issue_invitation: IssueInvitationHandler,
        renderer: EmailRenderer,
        mailer: Mailer,
        clock: Clock,
        teams_url: str,
    ) -> None:
        self._uow_factory = uow_factory
        self._teams = teams
        self._issue_invitation = issue_invitation
        self._renderer = renderer
        self._mailer = mailer
        self._clock = clock
        self._teams_url = teams_url.rstrip("/")

    async def handle(self, command: InviteToTeam) -> TeamInvitationOutcome:
        email = Email(command.email)
        full_name = command.full_name.strip()
        if not full_name:
            raise InvalidFullNameError("A person's name cannot be blank")
        team = await self._teams.get(command.team_id)
        if team is None:
            raise UnknownTeamError(f"Team {command.team_id} does not exist")

        async with self._uow_factory() as uow:
            account = await uow.users.get_by_email(email)
            inviter = await uow.users.get(command.inviter_user_id)
        inviter_name = inviter.full_name if inviter is not None else ""

        if account is None:
            await self._issue_invitation.handle(
                IssueInvitation(
                    team_id=command.team_id,
                    team_name=team.team_name,
                    email=email.value,
                    full_name=full_name,
                    role=command.role,
                    language=team.language,
                    created_by=command.inviter_membership_id,
                    inviter_name=inviter_name,
                )
            )
            logger.info("Team %s: an invitation was sent", command.team_id)
            return TeamInvitationOutcome.INVITATION_SENT

        if not account.is_active:
            raise AccountDisabledError(f"The account {account.id} is disabled")
        await self._add_the_account(command, team, account, inviter_name)
        logger.info("Team %s: user %s joined as %s", command.team_id, account.id, command.role)
        return TeamInvitationOutcome.MEMBER_ADDED

    async def _add_the_account(
        self, command: InviteToTeam, team: TeamContacts, account: AppUser, inviter_name: str
    ) -> None:
        """One transaction: the pending invitation closed, the membership and the notice.
        The notice is sent before committing, so if the mail server refuses it the person
        is not left in the team without knowing."""
        async with self._uow_factory() as uow:
            await release_pending_invitation(uow, command.team_id, account.email, self._clock.now())
            await uow.team_membership.add_member(
                team_id=command.team_id, user_id=account.id, role=command.role
            )
            rendered = self._renderer.render(
                "member_added",
                team.language,
                name=account.full_name,
                team_name=team.team_name,
                inviter_name=inviter_name,
                team_url=f"{self._teams_url}/{command.team_id}",
            )
            await self._mailer.send(
                EmailMessage(
                    to=account.email.value,
                    subject=rendered.subject,
                    text_body=rendered.text_body,
                    html_body=rendered.html_body,
                )
            )
            await uow.commit()
