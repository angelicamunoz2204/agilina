from collections.abc import Callable
from datetime import datetime
from uuid import UUID, uuid4

from agilina_api.identity.application.commands.issue_invitation.issue_invitation import (
    IssueInvitation,
)
from agilina_api.identity.application.dtos import IssuedInvitation
from agilina_api.identity.application.ports.outbound import (
    ActivationTokenGenerator,
    IdentityUnitOfWork,
)
from agilina_api.identity.domain.errors import PendingInvitationAlreadyExistsError
from agilina_api.identity.domain.invitation import Invitation
from agilina_api.identity.domain.value_objects import Email
from agilina_api.shared.application.ports import Clock, EmailMessage, EmailRenderer, Mailer


class IssueInvitationHandler:
    def __init__(  # noqa: PLR0913
        self,
        uow_factory: Callable[[], IdentityUnitOfWork],
        tokens: ActivationTokenGenerator,
        renderer: EmailRenderer,
        mailer: Mailer,
        clock: Clock,
        activation_url: str,
        new_id: Callable[[], UUID] = uuid4,
    ) -> None:
        self._uow_factory = uow_factory
        self._tokens = tokens
        self._renderer = renderer
        self._mailer = mailer
        self._clock = clock
        self._activation_url = activation_url
        self._new_id = new_id

    async def handle(self, command: IssueInvitation) -> IssuedInvitation:
        email = Email(command.email)
        now = self._clock.now()
        token = self._tokens.generate()

        async with self._uow_factory() as uow:
            await self._release_an_overdue_invitation(uow, command.team_id, email, now)

            invitation = Invitation.issue(
                invitation_id=self._new_id(),
                team_id=command.team_id,
                email=email,
                full_name=command.full_name,
                role=command.role,
                token_hash=token.hash(),
                created_by=command.created_by,
                now=now,
            )
            await uow.invitations.add(invitation)

            rendered = self._renderer.render(
                "invitation",
                command.language,
                name=invitation.full_name,
                team_name=command.team_name,
                inviter_name=command.inviter_name or "",
                activation_url=f"{self._activation_url}#t={token.value}",
                expires_on=invitation.expires_at.date().isoformat(),
            )
            # Sent before committing: if the server refuses, nothing is stored and the
            # operator can simply try again.
            await self._mailer.send(
                EmailMessage(
                    to=email.value,
                    subject=rendered.subject,
                    text_body=rendered.text_body,
                    html_body=rendered.html_body,
                )
            )
            await uow.commit()

        return IssuedInvitation(invitation_id=invitation.id, expires_at=invitation.expires_at)

    @staticmethod
    async def _release_an_overdue_invitation(
        uow: IdentityUnitOfWork, team_id: UUID, email: Email, now: datetime
    ) -> None:
        """A pending invitation past its deadline still blocks a new one (the index only
        allows one pending per email and team): store its expiry first. One that still
        works is an error."""
        existing = await uow.invitations.find_pending(team_id, email)
        if existing is None:
            return
        if not existing.expire_if_due(now):
            raise PendingInvitationAlreadyExistsError(
                f"Team {team_id} already has a valid invitation for {email}"
            )
        await uow.invitations.save(existing)
