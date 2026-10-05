"""Send a test email with the configured SMTP server.

    make mail-test to=address@example.com [lang=en]

It is how you check ``AGILINA_SMTP_*`` (Mailpit, Amazon SES, Gmail…) and see the email
design without waiting for a feature that sends email. It lives in ``bootstrap`` because
it wires the settings to the renderer and the SMTP adapter, like the application does.
"""

import argparse
import asyncio
import sys

from agilina_api.shared.application.ports import EmailMessage, MailDeliveryError
from agilina_api.shared.infrastructure.mail.renderer import JinjaEmailRenderer
from agilina_api.shared.infrastructure.mail.smtp_mailer import SmtpMailer
from agilina_api.shared.infrastructure.settings import Settings, get_settings
from agilina_shared.enums import Language


def build_test_email(settings: Settings, to: str, language: Language) -> EmailMessage:
    """The test email, rendered from the ``test`` template in ``language``."""
    rendered = JinjaEmailRenderer().render(
        "test",
        language,
        server=f"{settings.smtp_host}:{settings.smtp_port}",
        security=settings.smtp_security,
        sender=settings.mail_from,
    )
    return EmailMessage(
        to=to,
        subject=rendered.subject,
        text_body=rendered.text_body,
        html_body=rendered.html_body,
    )


async def send(to: str, language: Language) -> None:
    settings = get_settings()
    mailer = SmtpMailer(
        host=settings.smtp_host,
        port=settings.smtp_port,
        sender=settings.mail_from,
        username=settings.smtp_user,
        password=settings.smtp_password.get_secret_value(),
        security=settings.smtp_security,
    )
    await mailer.send(build_test_email(settings, to, language))
    print(
        f"Sent to {to} ({language.value}) via {settings.smtp_host}:{settings.smtp_port} "
        f"({settings.smtp_security}) as {settings.mail_from}"
    )


def main() -> int:
    settings = get_settings()
    parser = argparse.ArgumentParser(description="Send a test email with the configured SMTP.")
    parser.add_argument("--to", required=True, help="recipient address")
    parser.add_argument(
        "--lang",
        choices=[language.value for language in Language],
        default=settings.default_language.value,
        help="language of the email (default: AGILINA_DEFAULT_LANGUAGE)",
    )
    arguments = parser.parse_args()
    try:
        asyncio.run(send(arguments.to, Language(arguments.lang)))
    except MailDeliveryError as error:
        print(f"Not sent: {error}", file=sys.stderr)
        print(
            "Check AGILINA_SMTP_* in .env (see docs/entorno-local.md, section 'Correo').",
            file=sys.stderr,
        )
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
