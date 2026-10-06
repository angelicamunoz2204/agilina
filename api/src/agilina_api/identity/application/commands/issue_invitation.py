"""Issue an invitation and e-mail its link (HU-02; HU-06 and ``make invite`` use it too)."""

from collections.abc import Callable
from dataclasses import dataclass
from uuid import UUID, uuid4

from agilina_api.identity.application.commands.pending_invitation import (
    release_pending_invitation,
)
from agilina_api.identity.application.dtos import IssuedInvitation
from agilina_api.identity.application.ports.outbound import (
    ActivationTokenGenerator,
    IdentityUnitOfWork,
)
from agilina_api.identity.domain.invitation import Invitation
from agilina_api.identity.domain.value_objects import Email
from agilina_api.shared.application.ports import Clock, EmailMessage, EmailRenderer, Mailer
from agilina_shared.enums import Language, TeamRole


@dataclass(frozen=True)
class IssueInvitation:
    team_id: UUID
    team_name: str
    email: str
    full_name: str
    role: TeamRole
    language: Language
    """The language of the email: the team's."""
    created_by: UUID | None = None
    """The member who issues it, or ``None`` when the platform operator does (AD-22)."""
    inviter_name: str | None = None


class IssueInvitationHandler:
    """Issuing an invitation to someone who already has a pending one in the team replaces
    it: the previous link stops working (HU-06). ``make invite`` behaves the same."""

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
            revoked_previous = await release_pending_invitation(uow, command.team_id, email, now)

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

        return IssuedInvitation(
            invitation_id=invitation.id,
            expires_at=invitation.expires_at,
            revoked_previous=revoked_previous,
        )
