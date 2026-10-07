from enum import StrEnum


class Language(StrEnum):
    """Team attribute. Parameterizes the transcription model, the template set,
    the language model instructions, the synthesized voice and the language of
    the summary."""

    ES = "es"
    EN = "en"
