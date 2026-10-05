"""Cross-cutting ports used by the use cases of every context."""

from dataclasses import dataclass
from datetime import datetime
from types import TracebackType
from typing import Protocol, Self

from agilina_shared.enums import Language


class Clock(Protocol):
    """The current instant, always in UTC (AD-20).

    A port so that time-dependent rules (a link that expires after seven days)
    are tested without waiting.
    """

    def now(self) -> datetime: ...


class UnitOfWork(Protocol):
    """A transaction around one use case.

    Entering it opens the transaction; ``commit`` makes the changes permanent
    and leaving without committing rolls them back.
    """

    async def __aenter__(self) -> Self: ...

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> None: ...

    async def commit(self) -> None: ...

    async def rollback(self) -> None: ...


@dataclass(frozen=True)
class EmailMessage:
    """One email to one recipient. The sender is not part of it: it is configuration."""

    to: str
    subject: str
    text_body: str
    html_body: str | None = None


@dataclass(frozen=True)
class RenderedEmail:
    """The content of an email, ready to be addressed and sent."""

    subject: str
    text_body: str
    html_body: str


class MailDeliveryError(Exception):
    """The mail server did not accept the message. It never carries credentials."""


class Mailer(Protocol):
    """Sends an email.

    A port (AD-23): the use cases do not know which server delivers it. In development
    and in the CI it is Mailpit; in staging and production, whichever provider is
    configured (``AGILINA_SMTP_*``).
    """

    async def send(self, message: EmailMessage) -> None: ...


class EmailRenderer(Protocol):
    """Builds the content of an email from a named template, in a language.

    A port so that the use cases never deal with HTML or with a template engine: they
    ask for ``"invitation"`` in ``Language.ES`` with its parameters and get the
    subject, the plain-text version and the HTML version.
    """

    def render(self, template: str, language: Language, **params: object) -> RenderedEmail: ...
