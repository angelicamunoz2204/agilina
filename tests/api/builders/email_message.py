"""Builder of ``EmailMessage``."""

from dataclasses import dataclass, replace
from typing import Self

from agilina_api.shared.application.ports import EmailMessage


@dataclass(frozen=True)
class EmailMessageBuilder:
    """A plain-text message to Julián with the activation instructions."""

    to: str = "julian@example.test"
    subject: str = "Activa tu cuenta"
    text_body: str = "Abre el enlace."
    html_body: str | None = None

    def to_address(self, to: str) -> Self:
        return replace(self, to=to)

    def with_subject(self, subject: str) -> Self:
        return replace(self, subject=subject)

    def with_html(self, html_body: str) -> Self:
        return replace(self, html_body=html_body)

    def build(self) -> EmailMessage:
        return EmailMessage(
            to=self.to, subject=self.subject, text_body=self.text_body, html_body=self.html_body
        )
