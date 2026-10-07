import logging
from collections.abc import Callable
from uuid import UUID, uuid4

from agilina_api.identity.application.commands.activate_account.activate_account import (
    ActivateAccount,
)
from agilina_api.identity.application.dtos import ActivatedAccount
from agilina_api.identity.application.errors import (
    AccountAlreadyExistsError,
    InvitationNotFoundError,
)
from agilina_api.identity.application.ports.outbound import IdentityProvider, IdentityUnitOfWork
from agilina_api.identity.domain.errors import InvalidActivationTokenError
from agilina_api.identity.domain.user import AppUser
from agilina_api.identity.domain.value_objects import ActivationToken
from agilina_api.shared.application.ports import Clock

logger = logging.getLogger(__name__)


class ActivateAccountHandler:
    def __init__(
        self,
        uow_factory: Callable[[], IdentityUnitOfWork],
        identity_provider: IdentityProvider,
        clock: Clock,
        new_id: Callable[[], UUID] = uuid4,
    ) -> None:
        self._uow_factory = uow_factory
        self._identity_provider = identity_provider
        self._clock = clock
        self._new_id = new_id

    async def handle(self, command: ActivateAccount) -> ActivatedAccount:
        try:
            token = ActivationToken.parse(command.token)
        except InvalidActivationTokenError as error:
            raise InvitationNotFoundError("The link is not valid") from error
        now = self._clock.now()

        # The row is locked from here to the end: a second activation of the same link
        # waits and then finds it already used.
        async with self._uow_factory() as uow:
            invitation = await uow.invitations.get_by_token_hash(token.hash())
            if invitation is None:
                raise InvitationNotFoundError("No invitation has that token")

            # The state is checked first, in memory: nothing outside is touched for a link
            # that cannot be used (already used, expired or revoked).
            user_id = self._new_id()
            invitation.accept(user_id=user_id, now=now)

            if await uow.users.get_by_email(invitation.email) is not None:
                raise AccountAlreadyExistsError(
                    f"There is already an account for {invitation.email}"
                )

            subject = await self._identity_provider.create_user(
                email=invitation.email, full_name=invitation.full_name, password=command.password
            )
            try:
                # The user goes first: the invitation points to it with a foreign key.
                await uow.users.add(
                    AppUser.register(
                        user_id=user_id,
                        keycloak_subject=subject,
                        email=invitation.email,
                        full_name=invitation.full_name,
                        now=now,
                    )
                )
                await uow.team_membership.add_member(
                    team_id=invitation.team_id, user_id=user_id, role=invitation.role
                )
                await uow.invitations.save(invitation)
                await uow.commit()
            except BaseException:
                await self._undo_the_account(subject)
                raise

        return ActivatedAccount(
            user_id=user_id,
            team_id=invitation.team_id,
            email=invitation.email,
            role=invitation.role,
        )

    async def _undo_the_account(self, subject: str) -> None:
        """Compensation: the account exists in Keycloak but the activation did not commit."""
        try:
            await self._identity_provider.delete_user(subject)
        except Exception:
            # The original failure is what the caller must see; this one is only logged.
            logger.exception(
                "Could not remove the Keycloak account %s after a failed activation", subject
            )
