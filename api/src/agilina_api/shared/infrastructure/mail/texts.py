"""Texts of the emails, in the two languages of the product.

Like the spoken texts (``agilina_shared.i18n``), nothing user-facing is written inside
the templates: they only place these strings. A test fails if a template exists in one
language and not in the other. Values may use ``{{ parameter }}``, resolved at render time.
"""

from agilina_shared.enums import Language

LAYOUT: dict[Language, dict[str, str]] = {
    Language.ES: {
        "tagline": "Tu Scrum Master virtual para la Daily Stand-up",
        "footer": "Este es un mensaje automático de Agilina. No respondas a este correo.",
    },
    Language.EN: {
        "tagline": "Your virtual Scrum Master for the Daily Stand-up",
        "footer": "This is an automatic message from Agilina. Please do not reply to it.",
    },
}

TEMPLATES: dict[str, dict[Language, dict[str, str]]] = {
    "test": {
        Language.ES: {
            "subject": "Agilina: prueba de correo",
            "preheader": "Si ves este mensaje, el envío de correo de Agilina funciona.",
            "title": "El correo funciona",
            "intro": (
                "Este es un mensaje de prueba. Si lo ves con su diseño, el envío de "
                "correo de Agilina está bien configurado."
            ),
            "details": "Con qué se envió",
            "server": "Servidor",
            "security": "Seguridad",
            "security_none": "Sin cifrar (solo para pruebas)",
            "security_starttls": "Cifrado con STARTTLS",
            "security_tls": "Cifrado con TLS",
            "sender": "Remitente",
        },
        Language.EN: {
            "subject": "Agilina: email test",
            "preheader": "If you can see this message, Agilina's email delivery works.",
            "title": "Email delivery works",
            "intro": (
                "This is a test message. If you can see it with its design, Agilina's "
                "email delivery is configured correctly."
            ),
            "details": "How it was sent",
            "server": "Server",
            "security": "Security",
            "security_none": "Unencrypted (testing only)",
            "security_starttls": "Encrypted with STARTTLS",
            "security_tls": "Encrypted with TLS",
            "sender": "Sender",
        },
    },
}
