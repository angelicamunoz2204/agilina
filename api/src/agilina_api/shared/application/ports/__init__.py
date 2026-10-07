"""Cross-cutting ports used by the use cases of every context."""

from agilina_api.shared.application.ports.clock import Clock
from agilina_api.shared.application.ports.email_message import EmailMessage
from agilina_api.shared.application.ports.email_renderer import EmailRenderer
from agilina_api.shared.application.ports.mail_delivery_error import MailDeliveryError
from agilina_api.shared.application.ports.mailer import Mailer
from agilina_api.shared.application.ports.rendered_email import RenderedEmail
from agilina_api.shared.application.ports.unit_of_work import UnitOfWork

__all__ = [
    "Clock",
    "EmailMessage",
    "EmailRenderer",
    "MailDeliveryError",
    "Mailer",
    "RenderedEmail",
    "UnitOfWork",
]
