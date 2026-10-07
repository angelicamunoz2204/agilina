"""Create a team and invite its first admin, as the platform operator (AD-22).

    make invite tenant=acme team="Atlas" email=julian@example.com name="Julián Torres" \
        [lang=es] [role=admin]
    make invite tenant=acme team-id=<uuid> email=... name=...   # one more person for a team

The tenant (AD-29) is the organization the team belongs to: its database, its realm. ``lang``
is the team's language and, when it is not given, the tenant's.

There is no public registration, so the first admin of a team cannot invite themselves:
whoever operates the platform does it from here, with access to its database. The person
gets the usual invitation email and activates the account like anyone else.
"""

import argparse
import asyncio
import sys
from uuid import UUID

from agilina_api.bootstrap.container import Container, build_container
from agilina_api.identity.application.commands.issue_invitation import IssueInvitation
from agilina_api.shared.application.ports import MailDeliveryError
from agilina_api.shared.application.tenancy import Tenant
from agilina_api.shared.infrastructure.clock import SystemClock
from agilina_api.shared.infrastructure.database.session import (
    create_engine_for,
    create_session_factory,
)
from agilina_api.shared.infrastructure.settings import Settings, get_settings
from agilina_api.shared.infrastructure.tenancy.sql_tenant_directory import SqlTenantDirectory
from agilina_api.shared_kernel import DomainError
from agilina_api.teams.application.commands.create_team import CreateTeam
from agilina_shared.enums import Language, TeamRole


async def invite(
    container: Container,
    *,
    email: str,
    full_name: str,
    role: TeamRole,
    language: Language,
    team_name: str | None,
    team_id: UUID | None,
) -> None:
    if team_id is None:
        assert team_name is not None  # argparse guarantees one of the two
        team_id = await container.create_team.handle(CreateTeam(name=team_name, language=language))
        print(f"Created team '{team_name}' ({team_id})")
    else:
        summary = await container.team_queries.get_summary(team_id)
        if summary is None:
            raise DomainError(f"There is no team {team_id}")
        team_name, language = summary.name, summary.language

    issued = await container.issue_invitation.handle(
        IssueInvitation(
            team_id=team_id,
            team_name=team_name or "",
            email=email,
            full_name=full_name,
            role=role,
            language=language,
        )
    )
    print(f"Invitation {issued.invitation_id} sent to {email} as {role.value}")
    print(f"The link expires on {issued.expires_at.date().isoformat()} (UTC) and works once.")


async def find_tenant(settings: Settings, slug: str) -> Tenant:
    """The active tenant ``slug`` of the platform's catalog."""
    engine = create_engine_for(settings.platform_dsn)
    try:
        tenant = await SqlTenantDirectory(
            create_session_factory(engine), SystemClock()
        ).find_active(slug)
    finally:
        await engine.dispose()
    if tenant is None:
        raise DomainError(f"There is no active tenant '{slug}' (add it with make tenant-add)")
    return tenant


async def run(arguments: argparse.Namespace) -> None:
    settings = get_settings()
    tenant = await find_tenant(settings, arguments.tenant)
    container = build_container(settings, tenant)
    language = Language(arguments.lang) if arguments.lang else tenant.language
    try:
        await invite(
            container,
            email=arguments.email,
            full_name=arguments.name,
            role=TeamRole(arguments.role),
            language=language,
            team_name=arguments.team,
            team_id=UUID(arguments.team_id) if arguments.team_id else None,
        )
    finally:
        await container.aclose()


def main() -> int:
    parser = argparse.ArgumentParser(description="Invite a person to a team as the operator.")
    parser.add_argument(
        "--tenant", required=True, help="slug of the organization (make tenant-add)"
    )
    parser.add_argument("--email", required=True)
    parser.add_argument("--name", required=True, help="the person's full name")
    target = parser.add_mutually_exclusive_group(required=True)
    target.add_argument("--team", help="name of a NEW team to create")
    target.add_argument("--team-id", help="id of an existing team")
    parser.add_argument("--role", choices=[role.value for role in TeamRole], default="admin")
    parser.add_argument(
        "--lang",
        choices=[language.value for language in Language],
        default=None,
        help="language of the new team and of the email (default: the tenant's)",
    )
    arguments = parser.parse_args()
    try:
        asyncio.run(run(arguments))
    except MailDeliveryError as error:
        print(f"The invitation was not created, the email failed: {error}", file=sys.stderr)
        print("Is the SMTP server up? (make up, then check AGILINA_SMTP_*)", file=sys.stderr)
        return 1
    except DomainError as error:
        print(f"Not done: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
