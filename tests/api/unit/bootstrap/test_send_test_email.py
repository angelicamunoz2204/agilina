"""``make mail-test``: send a test email with the configured SMTP."""

import sys

import pytest

from agilina_api.bootstrap import send_test_email
from agilina_api.shared.application.ports import MailDeliveryError
from agilina_api.shared.infrastructure.settings import get_settings
from agilina_shared.enums import Language
from tests.api.doubles import FakeMailer


@pytest.fixture
def mailer(monkeypatch) -> FakeMailer:
    """Every ``SmtpMailer`` the command builds is this recording double."""
    recording = FakeMailer()
    monkeypatch.setattr(send_test_email, "SmtpMailer", lambda **options: recording)
    return recording


def test_the_email_is_rendered_in_the_requested_language():
    message = send_test_email.build_test_email(get_settings(), "ana@example.test", Language.EN)

    assert message.to == "ana@example.test"
    assert message.subject and message.text_body and message.html_body


async def test_sending_delivers_one_message_and_says_where(mailer, capsys):
    await send_test_email.send("ana@example.test", Language.ES)

    [message] = mailer.sent
    assert message.to == "ana@example.test"
    assert "Sent to ana@example.test (es)" in capsys.readouterr().out


def test_the_command_line_sends_to_the_given_address_and_succeeds(mailer, monkeypatch):
    monkeypatch.setattr(sys, "argv", ["mail-test", "--to", "ana@example.test", "--lang", "en"])

    assert send_test_email.main() == 0
    assert [m.to for m in mailer.sent] == ["ana@example.test"]


def test_a_mail_failure_is_explained_and_the_exit_code_says_so(mailer, monkeypatch, capsys):
    mailer.fail = True
    monkeypatch.setattr(sys, "argv", ["mail-test", "--to", "ana@example.test"])

    assert send_test_email.main() == 1
    assert "Not sent" in capsys.readouterr().err
    assert issubclass(MailDeliveryError, Exception)
