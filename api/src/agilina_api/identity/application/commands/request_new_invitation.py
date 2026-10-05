"""A person whose link no longer works asks for a new one (HU-02, criterion 5)."""

import logging
from collections.abc import Callable
from dataclasses import dataclass

from agilina_api.identity.application.errors import (
    InvitationNotFoundError,
    InvitationStillValidError,
    NoAdminsToNotifyError,
)
from agilina_api.identity.application.ports.outbound import (
    IdentityUnitOfWork,
    TeamContactsDirectory,
)
from agilina_api.identity.domain.errors import InvalidActivationTokenError
from agilina_api.identity.domain.invitation import InvitationStatus
from agilina_api.identity.domain.value_objects import ActivationToken
from agilina_api.shared.application.ports import (
    Clock,
    EmailMessage,
    EmailRenderer,
    MailDeliveryError,
    Mailer,
)

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class RequestNewInvitation:
    token: str


class RequestNewInvitationHandler:
    def __init__(  # noqa: PLR0913
        self,
        uow_factory: Callable[[], IdentityUnitOfWork],
        contacts: TeamContactsDirectory,
        renderer: EmailRenderer,
        mailer: Mailer,
        clock: Clock,
    ) -> None:
        self._uow_factory = uow_factory
        self._contacts = contacts
        self._renderer = renderer
        self._mailer = mailer
        self._clock = clock

    async def handle(self, command: RequestNewInvitation) -> None:
        """Tell the team's admins that this person needs a new invitation.

        Nobody can issue it on their own: only an admin invites (there is no public
        registration), so the request goes to them.
        """
        try:
            token = ActivationToken.parse(command.token)
        except InvalidActivationTokenError as error:
            raise InvitationNotFoundError("The link is not valid") from error

        async with self._uow_factory() as uow:
            invitation = await uow.invitations.get_by_token_hash(token.hash())
        if invitation is None:
            raise InvitationNotFoundError("No invitation has that token")

        state = invitation.state_at(self._clock.now())
        if state is InvitationStatus.PENDING:
            raise InvitationStillValidError("The link still works")

        team = await self._contacts.get(invitation.team_id)
        if team is None or not team.admins:
            raise NoAdminsToNotifyError(f"Team {invitation.team_id} has no admin to notify")

        delivered = 0
        for admin in team.admins:
            rendered = self._renderer.render(
                "new_invitation_request",
                team.language,
                admin_name=admin.full_name,
                requester_name=invitation.full_name,
                requester_email=invitation.email.value,
                team_name=team.team_name,
                reason=state.value,
            )
            try:
                await self._mailer.send(
                    EmailMessage(
                        to=admin.email.value,
                        subject=rendered.subject,
                        text_body=rendered.text_body,
                        html_body=rendered.html_body,
                    )
                )
                delivered += 1
            except MailDeliveryError:
                logger.warning("Could not notify an admin of team %s", invitation.team_id)
        if delivered == 0:
            raise MailDeliveryError("No admin could be notified")
