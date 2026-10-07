from typing import Protocol

from agilina_api.shared.application.ports.email_message import EmailMessage


class Mailer(Protocol):
    """Sends an email.

    A port (AD-23): the use cases do not know which server delivers it. In development
    and in the CI it is Mailpit; in staging and production, whichever provider is
    configured (``AGILINA_SMTP_*``).
    """

    async def send(self, message: EmailMessage) -> None: ...
