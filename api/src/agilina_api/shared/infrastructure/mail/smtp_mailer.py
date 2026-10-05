"""SMTP implementation of the ``Mailer`` port.

It speaks plain SMTP, so it works with any server: Mailpit in development and in the
CI, Amazon SES, Gmail or any other provider in staging and production. Which one is
used is decided only by configuration (``AGILINA_SMTP_*``), never by code (AD-23).
"""

import asyncio
import smtplib
import ssl
from email.message import EmailMessage as MimeMessage
from email.utils import formatdate, make_msgid
from typing import Literal

from agilina_api.shared.application.ports import EmailMessage, MailDeliveryError, Mailer
from agilina_api.shared.infrastructure.logging_setup import get_logger

logger = get_logger(__name__)

SmtpSecurity = Literal["none", "starttls", "tls"]
"""``none``: plain (Mailpit). ``starttls``: upgrade the connection, usually port 587
(Amazon SES, Gmail). ``tls``: encrypted from the start, usually port 465."""


def mask_email(address: str) -> str:
    """``julian@example.test`` → ``j***@example.test``: logs never carry a full address."""
    local, _, domain = address.partition("@")
    return f"{local[:1]}***@{domain}" if domain else "***"


class SmtpMailer(Mailer):
    def __init__(
        self,
        *,
        host: str,
        port: int,
        sender: str,
        username: str = "",
        password: str = "",
        security: SmtpSecurity = "none",
        timeout: float = 10.0,
    ) -> None:
        self._host = host
        self._port = port
        self._sender = sender
        self._username = username
        self._password = password
        self._security = security
        self._timeout = timeout

    async def send(self, message: EmailMessage) -> None:
        mime = self._build(message)  # a malformed header fails here, before any connection
        try:
            await asyncio.to_thread(self._deliver, mime)
        except (smtplib.SMTPException, OSError) as error:
            # Only the kind of failure is logged: the provider's reply may echo the
            # credentials or the full address.
            logger.warning(
                "Email to %s was not delivered via %s:%s (%s)",
                mask_email(message.to),
                self._host,
                self._port,
                type(error).__name__,
            )
            raise MailDeliveryError(
                f"The mail server {self._host}:{self._port} did not accept the message "
                f"({type(error).__name__})"
            ) from error
        logger.info("Email to %s sent via %s:%s", mask_email(message.to), self._host, self._port)

    def _build(self, message: EmailMessage) -> MimeMessage:
        mime = MimeMessage()
        mime["From"] = self._sender
        mime["To"] = message.to
        mime["Subject"] = message.subject
        mime["Date"] = formatdate(localtime=False)
        mime["Message-ID"] = make_msgid()
        mime.set_content(message.text_body)
        if message.html_body is not None:
            mime.add_alternative(message.html_body, subtype="html")
        return mime

    def _deliver(self, mime: MimeMessage) -> None:
        context = ssl.create_default_context()
        client: smtplib.SMTP
        if self._security == "tls":
            client = smtplib.SMTP_SSL(
                self._host, self._port, timeout=self._timeout, context=context
            )
        else:
            client = smtplib.SMTP(self._host, self._port, timeout=self._timeout)
        with client:
            if self._security == "starttls":
                client.starttls(context=context)
            if self._username:
                client.login(self._username, self._password)
            client.send_message(mime)
