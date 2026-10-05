"""Doubles of the ports: in-memory implementations the use case tests run against."""

from tests.api.doubles.clock import FakeClock
from tests.api.doubles.identity import (
    FakeIdentityProvider,
    FakeIdentityUnitOfWork,
    FakeInvitationQueries,
    FakeTeamContactsDirectory,
    FakeTeamMembership,
    FakeTokenGenerator,
    InMemoryInvitationRepository,
    InMemoryUserRepository,
)
from tests.api.doubles.mail import FakeMailer, FakeRenderer
from tests.api.doubles.teams import FakeTeamsUnitOfWork, InMemoryTeamRepository

__all__ = [
    "FakeClock",
    "FakeIdentityProvider",
    "FakeIdentityUnitOfWork",
    "FakeInvitationQueries",
    "FakeMailer",
    "FakeRenderer",
    "FakeTeamContactsDirectory",
    "FakeTeamMembership",
    "FakeTeamsUnitOfWork",
    "FakeTokenGenerator",
    "InMemoryInvitationRepository",
    "InMemoryTeamRepository",
    "InMemoryUserRepository",
]
