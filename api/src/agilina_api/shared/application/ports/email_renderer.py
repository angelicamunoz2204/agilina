from typing import Protocol

from agilina_api.shared.application.ports.rendered_email import RenderedEmail
from agilina_shared.enums import Language


class EmailRenderer(Protocol):
    """Builds the content of an email from a named template, in a language.

    A port so that the use cases never deal with HTML or with a template engine: they
    ask for ``"invitation"`` in ``Language.ES`` with its parameters and get the
    subject, the plain-text version and the HTML version.
    """

    def render(self, template: str, language: Language, **params: object) -> RenderedEmail: ...
