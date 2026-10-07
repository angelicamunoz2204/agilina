from dataclasses import dataclass


@dataclass(frozen=True)
class EmailMessage:
    """One email to one recipient. The sender is not part of it: it is configuration."""

    to: str
    subject: str
    text_body: str
    html_body: str | None = None
