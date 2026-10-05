"""Dependency providers declared by the identity presentation layer.

The composition root overrides them with the real handlers, so this layer never imports
the infrastructure one.
"""

from agilina_api.identity.application.commands.activate_account import ActivateAccountHandler
from agilina_api.identity.application.commands.request_new_invitation import (
    RequestNewInvitationHandler,
)
from agilina_api.identity.application.queries.get_invitation_status import (
    GetInvitationStatusHandler,
)


def get_invitation_status_handler() -> GetInvitationStatusHandler:
    raise NotImplementedError("Wired by the composition root")


def get_activate_account_handler() -> ActivateAccountHandler:
    raise NotImplementedError("Wired by the composition root")


def get_request_new_invitation_handler() -> RequestNewInvitationHandler:
    raise NotImplementedError("Wired by the composition root")
