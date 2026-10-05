"""Doubles of the mail ports: what was sent, and what the renderer produced."""

from agilina_api.shared.application.ports import (
    EmailMessage,
    EmailRenderer,
    MailDeliveryError,
    RenderedEmail,
)
from agilina_shared.enums import Language


class FakeMailer:
    def __init__(self) -> None:
        self.sent: list[EmailMessage] = []
        self.fail = False

    async def send(self, message: EmailMessage) -> None:
        if self.fail:
            raise MailDeliveryError("the server is down")
        self.sent.append(message)


class FakeRenderer(EmailRenderer):
    """Renders every template as ``name|language|key=value,...`` so a test can assert on it."""

    def render(self, template: str, language: Language, **params: object) -> RenderedEmail:
        body = ",".join(f"{key}={value}" for key, value in sorted(params.items()))
        return RenderedEmail(
            subject=f"{template}:{language.value}",
            text_body=f"{template}|{language.value}|{body}",
            html_body=f"<p>{template}|{language.value}|{body}</p>",
        )
