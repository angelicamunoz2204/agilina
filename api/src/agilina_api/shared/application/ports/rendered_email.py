from dataclasses import dataclass


@dataclass(frozen=True)
class RenderedEmail:
    """The content of an email, ready to be addressed and sent."""

    subject: str
    text_body: str
    html_body: str
