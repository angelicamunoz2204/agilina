"""The ``AppUser`` aggregate: who a person is in Agilina.

Credentials and sessions live in Keycloak (AD-12); this only anchors the domain's
references. ``keycloak_subject`` is the ``sub`` claim of the OIDC token, the single link
with the identity provider.
"""

from datetime import datetime
from uuid import UUID

from agilina_api.identity.domain.errors import InvalidFullNameError
from agilina_api.identity.domain.value_objects import Email
from agilina_api.shared_kernel import AggregateRoot


class AppUser(AggregateRoot[UUID]):
    def __init__(
        self,
        *,
        user_id: UUID,
        keycloak_subject: str,
        email: Email,
        full_name: str,
        is_active: bool,
        created_at: datetime,
    ) -> None:
        super().__init__(user_id)
        self._keycloak_subject = keycloak_subject
        self._email = email
        self._full_name = full_name
        self._is_active = is_active
        self._created_at = created_at

    @classmethod
    def register(
        cls,
        *,
        user_id: UUID,
        keycloak_subject: str,
        email: Email,
        full_name: str,
        now: datetime,
    ) -> "AppUser":
        name = full_name.strip()
        if not name:
            raise InvalidFullNameError("A person's name cannot be blank")
        if not keycloak_subject.strip():
            raise ValueError("A user needs the Keycloak subject that identifies them")
        return cls(
            user_id=user_id,
            keycloak_subject=keycloak_subject.strip(),
            email=email,
            full_name=name,
            is_active=True,
            created_at=now,
        )

    @property
    def keycloak_subject(self) -> str:
        return self._keycloak_subject

    @property
    def email(self) -> Email:
        return self._email

    @property
    def full_name(self) -> str:
        return self._full_name

    @property
    def is_active(self) -> bool:
        return self._is_active

    @property
    def created_at(self) -> datetime:
        return self._created_at
