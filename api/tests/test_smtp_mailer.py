"""The SMTP mailer is tested against a fake ``smtplib``: no network and no server.

What a real server adds (STARTTLS negotiation, authentication) is checked with
``make mail-test`` against Mailpit or the configured provider.
"""

from email.message import EmailMessage as MimeMessage
from typing import Any, ClassVar, Self

import pytest

from agilina_api.shared.application.ports import EmailMessage, MailDeliveryError
from agilina_api.shared.infrastructure.mail import smtp_mailer
from agilina_api.shared.infrastructure.mail.smtp_mailer import SmtpMailer, mask_email

SENDER = "Agilina <no-reply@agilina.local>"


class FakeSmtp:
    """Records what the mailer does, in order, in ``calls``."""

    instances: ClassVar[list["FakeSmtp"]] = []
    fail_with: ClassVar[Exception | None] = None

    def __init__(self, host: str, port: int, **options: Any) -> None:
        self.kind = type(self).__name__
        self.host, self.port, self.options = host, port, options
        self.calls: list[str] = []
        self.sent: list[MimeMessage] = []
        FakeSmtp.instances.append(self)

    def __enter__(self) -> Self:
        return self

    def __exit__(self, *exc: object) -> None:
        return None

    def starttls(self, **options: Any) -> None:
        self.calls.append("starttls")

    def login(self, user: str, password: str) -> None:
        self.calls.append(f"login:{user}")

    def send_message(self, message: MimeMessage) -> None:
        if FakeSmtp.fail_with is not None:
            raise FakeSmtp.fail_with
        self.calls.append("send")
        self.sent.append(message)


class FakeSmtpSsl(FakeSmtp):
    pass


@pytest.fixture(autouse=True)
def fake_smtplib(monkeypatch: pytest.MonkeyPatch) -> None:
    FakeSmtp.instances = []
    FakeSmtp.fail_with = None
    monkeypatch.setattr(smtp_mailer.smtplib, "SMTP", FakeSmtp)
    monkeypatch.setattr(smtp_mailer.smtplib, "SMTP_SSL", FakeSmtpSsl)


def _mailer(**overrides: Any) -> SmtpMailer:
    options: dict[str, Any] = {"host": "mailpit", "port": 1025, "sender": SENDER}
    options.update(overrides)
    return SmtpMailer(**options)


def _message(**overrides: Any) -> EmailMessage:
    fields: dict[str, Any] = {
        "to": "julian@example.test",
        "subject": "Activa tu cuenta",
        "text_body": "Abre el enlace.",
    }
    fields.update(overrides)
    return EmailMessage(**fields)


async def test_a_plain_server_gets_the_message_without_tls_or_login():
    await _mailer().send(_message())

    smtp = FakeSmtp.instances[0]
    assert smtp.kind == "FakeSmtp"
    assert (smtp.host, smtp.port) == ("mailpit", 1025)
    assert smtp.calls == ["send"]


async def test_the_message_carries_sender_recipient_subject_and_body():
    await _mailer().send(_message())

    sent = FakeSmtp.instances[0].sent[0]
    assert sent["From"] == SENDER
    assert sent["To"] == "julian@example.test"
    assert sent["Subject"] == "Activa tu cuenta"
    assert sent["Message-ID"] and sent["Date"]
    assert "Abre el enlace." in sent.get_content()


async def test_starttls_runs_before_login_and_login_before_sending():
    mailer = _mailer(
        host="email-smtp.us-east-1.amazonaws.com",
        port=587,
        username="AKIA-EXAMPLE",
        password="secret",
        security="starttls",
    )

    await mailer.send(_message())

    assert FakeSmtp.instances[0].calls == ["starttls", "login:AKIA-EXAMPLE", "send"]


async def test_implicit_tls_uses_the_ssl_connection():
    await _mailer(port=465, security="tls").send(_message())

    assert FakeSmtp.instances[0].kind == "FakeSmtpSsl"
    assert "starttls" not in FakeSmtp.instances[0].calls


async def test_an_html_body_is_sent_as_an_alternative_to_the_text():
    await _mailer().send(_message(html_body="<p>Abre el <a href='#'>enlace</a>.</p>"))

    sent = FakeSmtp.instances[0].sent[0]
    assert sent.get_content_type() == "multipart/alternative"
    assert [part.get_content_type() for part in sent.iter_parts()] == ["text/plain", "text/html"]


async def test_a_server_failure_becomes_a_delivery_error_without_leaking_credentials():
    FakeSmtp.fail_with = smtp_mailer.smtplib.SMTPRecipientsRefused({"x@y.test": (554, b"denied")})

    with pytest.raises(MailDeliveryError) as raised:
        await _mailer(username="AKIA-EXAMPLE", password="top-secret", security="starttls").send(
            _message()
        )

    assert "top-secret" not in str(raised.value)
    assert "AKIA-EXAMPLE" not in str(raised.value)
    assert "mailpit:1025" in str(raised.value)


async def test_a_network_failure_becomes_a_delivery_error():
    FakeSmtp.fail_with = ConnectionRefusedError()

    with pytest.raises(MailDeliveryError):
        await _mailer().send(_message())


async def test_a_header_injection_attempt_is_rejected_before_connecting():
    with pytest.raises(ValueError):  # noqa: PT011 - the stdlib raises ValueError
        await _mailer().send(_message(subject="Hola\r\nBcc: attacker@example.test"))

    assert FakeSmtp.instances == []


def test_addresses_are_masked_for_the_logs():
    assert mask_email("julian@example.test") == "j***@example.test"
    assert mask_email("not-an-address") == "***"
