"""Jinja2 implementation of the ``EmailRenderer`` port.

Each email is three files in ``templates/``: ``<name>.html`` (extends ``layout.html``),
``<name>.txt`` (the plain-text alternative that every client without HTML shows) and its
texts in ``texts.py``. HTML is autoescaped, so a value such as a person's name can never
inject markup; a missing parameter fails loudly instead of rendering a half-empty email.
"""

from pathlib import Path

from jinja2 import Environment, FileSystemLoader, StrictUndefined, select_autoescape

from agilina_api.shared.application.ports import EmailRenderer, RenderedEmail
from agilina_api.shared.infrastructure.mail.texts import LAYOUT, TEMPLATES
from agilina_api.shared.infrastructure.mail.theme import DARK, FONTS, LIGHT
from agilina_shared.enums import Language

TEMPLATES_DIR = Path(__file__).parent / "templates"


class JinjaEmailRenderer(EmailRenderer):
    def __init__(self, templates_dir: Path = TEMPLATES_DIR) -> None:
        loader = FileSystemLoader(templates_dir)
        self._html = Environment(
            loader=loader,
            autoescape=select_autoescape(["html"]),
            undefined=StrictUndefined,
            trim_blocks=True,
            lstrip_blocks=True,
        )
        # Plain text and subjects are not HTML: escaping them would show "&amp;".
        self._text = Environment(
            loader=loader,
            autoescape=False,  # noqa: S701 - plain text and subjects, not HTML
            undefined=StrictUndefined,
            trim_blocks=True,
            lstrip_blocks=True,
        )

    def render(self, template: str, language: Language, **params: object) -> RenderedEmail:
        try:
            texts = TEMPLATES[template][language]
        except KeyError as error:
            raise KeyError(f"No email template '{template}' for language '{language}'") from error

        base = {
            "layout": LAYOUT[language],
            "lang": language.value,
            "c": LIGHT,
            "d": DARK,
            "fonts": FONTS,
            **params,
        }
        # The texts may carry placeholders ("Hola {{ name }}"): they are filled in as plain
        # text first, and the HTML template escapes the result when it prints it.
        resolved = {key: self._text.from_string(value).render(base) for key, value in texts.items()}
        context = {**base, "t": resolved}
        subject = resolved["subject"]
        return RenderedEmail(
            subject=subject,
            text_body=self._text.get_template(f"{template}.txt").render(context),
            html_body=self._html.get_template(f"{template}.html").render(context),
        )
