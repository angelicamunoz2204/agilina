"""Translate between ORM rows and domain entities, in both directions."""

from agilina_api.identity.domain.invitation import Invitation
from agilina_api.identity.domain.user import AppUser
from agilina_api.identity.domain.value_objects import Email, TokenHash
from agilina_api.identity.infrastructure.persistence.orm_models import AppUserRow, InvitationRow


def invitation_to_domain(row: InvitationRow) -> Invitation:
    return Invitation(
        invitation_id=row.id,
        team_id=row.team_id,
        email=Email(row.email),
        full_name=row.full_name,
        role=row.role,
        token_hash=TokenHash(row.token_hash),
        status=row.status,
        expires_at=row.expires_at,
        created_by=row.created_by,
        created_at=row.created_at,
        accepted_at=row.accepted_at,
        accepted_user_id=row.accepted_user_id,
    )


def invitation_to_row(invitation: Invitation) -> InvitationRow:
    return InvitationRow(
        id=invitation.id,
        team_id=invitation.team_id,
        email=invitation.email.value,
        full_name=invitation.full_name,
        role=invitation.role,
        token_hash=invitation.token_hash.value,
        status=invitation.status,
        expires_at=invitation.expires_at,
        created_by=invitation.created_by,
        accepted_at=invitation.accepted_at,
        accepted_user_id=invitation.accepted_user_id,
        created_at=invitation.created_at,
    )


def user_to_domain(row: AppUserRow) -> AppUser:
    return AppUser(
        user_id=row.id,
        keycloak_subject=row.keycloak_subject,
        email=Email(row.email),
        full_name=row.full_name,
        is_active=row.is_active,
        created_at=row.created_at,
    )


def user_to_row(user: AppUser) -> AppUserRow:
    return AppUserRow(
        id=user.id,
        keycloak_subject=user.keycloak_subject,
        email=user.email.value,
        full_name=user.full_name,
        is_active=user.is_active,
        created_at=user.created_at,
    )
