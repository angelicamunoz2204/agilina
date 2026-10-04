"""Emails are rendered from templates, never written inside the code."""

import pytest
from jinja2 import UndefinedError

from agilina_api.bootstrap.send_test_email import build_test_email
from agilina_api.shared.infrastructure.mail.renderer import TEMPLATES_DIR, JinjaEmailRenderer
from agilina_api.shared.infrastructure.mail.texts import LAYOUT, TEMPLATES
from agilina_api.shared.infrastructure.settings import Settings
from agilina_shared.enums import Language

PARAMS = {
    "server": "mailpit:1025",
    "security": "none",
    "sender": "Agilina <no-reply@agilina.local>",
}


def _render(language: Language = Language.ES, **overrides: object):
    return JinjaEmailRenderer().render("test", language, **{**PARAMS, **overrides})


def test_the_html_is_a_complete_document_in_the_requested_language():
    html = _render(Language.ES).html_body

    assert html.lstrip().lower().startswith("<!doctype html>")
    assert '<html lang="es">' in html
    assert "El correo funciona" in html
    assert '<html lang="en">' in _render(Language.EN).html_body


def test_each_language_gets_its_own_subject_and_texts():
    spanish, english = _render(Language.ES), _render(Language.EN)

    assert spanish.subject == "Agilina: prueba de correo"
    assert english.subject == "Agilina: email test"
    assert "Servidor" in spanish.html_body and "Server" in english.html_body


def test_the_values_are_shown_in_both_the_html_and_the_text_versions():
    rendered = _render()

    for version in (rendered.html_body, rendered.text_body):
        assert "mailpit:1025" in version


def test_the_text_version_is_plain_text_without_markup():
    text = _render(sender="Agilina <no-reply@agilina.local>").text_body

    assert "<html" not in text and "<table" not in text
    assert "Agilina <no-reply@agilina.local>" in text  # not escaped: it is not HTML


def test_the_security_mode_is_shown_as_a_readable_label_in_each_language():
    assert "Sin cifrar" in _render(Language.ES, security="none").html_body
    assert "Cifrado con STARTTLS" in _render(Language.ES, security="starttls").text_body
    assert "Encrypted with TLS" in _render(Language.EN, security="tls").html_body


def test_html_values_are_escaped_so_they_cannot_inject_markup():
    html = _render(sender='<script>alert("x")</script>', server="a&b").html_body

    assert "<script>" not in html
    assert "&lt;script&gt;" in html
    assert "a&amp;b" in html


def test_a_missing_parameter_fails_instead_of_rendering_a_half_empty_email():
    with pytest.raises(UndefinedError):
        JinjaEmailRenderer().render("test", Language.ES, server="x", security="none")


def test_an_unknown_template_fails_with_a_clear_error():
    with pytest.raises(KeyError, match="nope"):
        JinjaEmailRenderer().render("nope", Language.ES)


def test_the_design_does_not_depend_on_remote_resources():
    """Clients block remote images and stylesheets by default: the email must stand alone."""
    html = _render().html_body.lower()

    assert "<img" not in html and "<link" not in html and "@import" not in html


def test_every_template_exists_in_both_languages_with_the_same_texts():
    for name, translations in TEMPLATES.items():
        assert set(translations) == set(Language), name
        assert translations[Language.ES].keys() == translations[Language.EN].keys(), name
    assert LAYOUT[Language.ES].keys() == LAYOUT[Language.EN].keys()


def test_every_template_has_an_html_and_a_text_file():
    for name in TEMPLATES:
        assert (TEMPLATES_DIR / f"{name}.html").is_file(), name
        assert (TEMPLATES_DIR / f"{name}.txt").is_file(), name


def test_the_test_email_is_built_from_the_settings_and_addressed_to_the_recipient():
    settings = Settings(_env_file=None, smtp_host="smtp.example.test", smtp_port=587)  # type: ignore[call-arg]

    message = build_test_email(settings, "julian@example.test", Language.EN)

    assert message.to == "julian@example.test"
    assert message.subject == "Agilina: email test"
    assert message.html_body and "smtp.example.test:587" in message.html_body
    assert "smtp.example.test:587" in message.text_body
