from agilina_api.identity.application.dtos import InvitationStatusView
from agilina_api.identity.application.errors import InvitationNotFoundError
from agilina_api.identity.application.ports.outbound import InvitationQueries
from agilina_api.identity.application.queries.get_invitation_status.get_invitation_status import (
    GetInvitationStatus,
)
from agilina_api.identity.domain.errors import InvalidActivationTokenError
from agilina_api.identity.domain.value_objects import ActivationToken
from agilina_api.shared.application.ports import Clock


class GetInvitationStatusHandler:
    def __init__(self, queries: InvitationQueries, clock: Clock) -> None:
        self._queries = queries
        self._clock = clock

    async def handle(self, query: GetInvitationStatus) -> InvitationStatusView:
        """The status at this moment, whatever it is (valid, used, expired…). Deciding how
        to show each one is the interface's job; only a link that matches nothing fails."""
        try:
            token = ActivationToken.parse(query.token)
        except InvalidActivationTokenError as error:
            raise InvitationNotFoundError("The link is not valid") from error
        view = await self._queries.get_status(token.hash(), self._clock.now())
        if view is None:
            raise InvitationNotFoundError("No invitation has that token")
        return view
