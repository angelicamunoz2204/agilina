"""Builders of the read DTOs ``Contact`` and ``TeamContacts``."""

from dataclasses import dataclass, replace
from typing import Self

from agilina_api.identity.application.dtos import Contact, TeamContacts
from agilina_api.identity.domain.value_objects import Email
from agilina_shared.enums import Language
from tests.api.builders.defaults import TEAM_NAME


@dataclass(frozen=True)
class ContactBuilder:
    email: str = "admin@example.test"
    full_name: str = "Admin"

    def with_email(self, email: str) -> Self:
        return replace(self, email=email)

    def named(self, full_name: str) -> Self:
        return replace(self, full_name=full_name)

    def build(self) -> Contact:
        return Contact(email=Email(self.email), full_name=self.full_name)


@dataclass(frozen=True)
class TeamContactsBuilder:
    """Team Atlas, in Spanish, with one admin (the default one) to tell."""

    team_name: str = TEAM_NAME
    language: Language = Language.ES
    admins: tuple[Contact, ...] = (ContactBuilder().build(),)

    def named(self, team_name: str) -> Self:
        return replace(self, team_name=team_name)

    def in_language(self, language: Language) -> Self:
        return replace(self, language=language)

    def with_admins(self, *admins: Contact) -> Self:
        return replace(self, admins=admins)

    def without_admins(self) -> Self:
        return replace(self, admins=())

    def build(self) -> TeamContacts:
        return TeamContacts(team_name=self.team_name, language=self.language, admins=self.admins)
