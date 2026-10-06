"""The invitations HTTP API, with in-memory doubles behind the use cases (no database): the
public HU-02 routes and the admin's invitation to a team (HU-06)."""

import pytest
from httpx import ASGITransport, AsyncClient

from agilina_api.bootstrap.app import create_app
from agilina_api.identity.application.commands.activate_account import ActivateAccountHandler
from agilina_api.identity.application.commands.invite_to_team import InviteToTeamHandler
from agilina_api.identity.application.commands.issue_invitation import IssueInvitationHandler
from agilina_api.identity.application.commands.request_new_invitation import (
    RequestNewInvitationHandler,
)
from agilina_api.identity.application.queries.get_invitation_status import (
    GetInvitationStatusHandler,
)
from agilina_api.identity.domain.errors import AlreadyTeamMemberError
from agilina_api.identity.domain.invitation import InvitationStatus
from agilina_api.identity.presentation.http import dependencies as deps
from agilina_api.shared.presentation.http.access import get_authenticated_users, get_team_access
from agilina_shared.enums import TeamRole
from tests.api.builders import (
    PASSWORD,
    TOKEN,
    AppUserBuilder,
    ContactBuilder,
    InvitationBuilder,
    TeamContactsBuilder,
    next_id,
)
from tests.api.doubles import (
    FakeAuthenticatedUsers,
    FakeClock,
    FakeIdentityProvider,
    FakeIdentityUnitOfWork,
    FakeInvitationQueries,
    FakeMailer,
    FakeRenderer,
    FakeTeamAccess,
    FakeTeamContactsDirectory,
    FakeTokenGenerator,
)


def _returning(handler):
    """A provider that hands back this very object. (A lambda with the handler as a default
    argument would not do: FastAPI reads that default as a parameter and copies it.)"""
    return lambda: handler


class Api:
    def __init__(self) -> None:
        self.uow = FakeIdentityUnitOfWork()
        self.provider = FakeIdentityProvider()
        self.mailer = FakeMailer()
        self.clock = FakeClock()
        self.team_id = next_id()
        diego = ContactBuilder().with_email("diego@example.test").named("Diego").build()
        team = TeamContactsBuilder().with_admins(diego).build()
        contacts = FakeTeamContactsDirectory({self.team_id: team})
        app = create_app()
        factory = self.uow.factory()
        handlers = {
            deps.get_invitation_status_handler: GetInvitationStatusHandler(
                FakeInvitationQueries(self.uow.invitations), self.clock
            ),
            deps.get_activate_account_handler: ActivateAccountHandler(
                factory, self.provider, self.clock
            ),
            deps.get_request_new_invitation_handler: RequestNewInvitationHandler(
                factory, contacts, FakeRenderer(), self.mailer, self.clock
            ),
        }
        for provider, handler in handlers.items():
            app.dependency_overrides[provider] = _returning(handler)
        self.app = app

    async def invite(self) -> None:
        """Julián has a pending invitation to join the team as an admin."""
        await InvitationBuilder().for_team(self.team_id).as_admin().saved_in(self.uow.invitations)

    def client(self) -> AsyncClient:
        return AsyncClient(transport=ASGITransport(app=self.app), base_url="http://tests")


@pytest.fixture
async def api() -> Api:
    api = Api()
    await api.invite()
    return api


async def post(api: Api, path: str, **body):
    async with api.client() as client:
        return await client.post(f"/v1/invitations/{path}", json=body)


# ---------------------------------------------------------------------- status --
async def test_a_valid_link_reports_who_it_is_for(api):
    response = await post(api, "status", token=TOKEN)

    assert response.status_code == 200
    assert response.json() == {
        "email": "julian@example.test",
        "full_name": "Julián Torres",
        "role": "admin",
        "status": "pending",
        "expires_at": "2026-10-11T12:00:00Z",
    }
    assert response.headers["cache-control"] == "no-store"


async def test_a_used_link_is_gone_with_its_own_code(api):
    await post(api, "activate", token=TOKEN, password=PASSWORD, confirmation=PASSWORD)

    response = await post(api, "status", token=TOKEN)

    assert response.status_code == 410 and response.json()["code"] == "invitation_used"


async def test_an_expired_link_is_gone_with_its_own_code(api):
    api.clock.advance(days=8)

    response = await post(api, "status", token=TOKEN)

    assert response.status_code == 410 and response.json()["code"] == "invitation_expired"


@pytest.mark.parametrize("token", ["", "short", "Z" * 43, "x" * 300])
async def test_an_altered_or_unknown_link_is_not_found(api, token):
    response = await post(api, "status", token=token)

    assert response.status_code in (404, 422)  # 422: too long for the schema, still not a link
    if response.status_code == 404:
        assert response.json()["code"] == "invitation_not_found"


# -------------------------------------------------------------------- activate --
async def test_activating_creates_the_account_and_says_where_to_go_next(api):
    response = await post(api, "activate", token=TOKEN, password=PASSWORD, confirmation=PASSWORD)

    assert response.status_code == 201
    assert response.json() == {
        "email": "julian@example.test",
        "team_id": str(api.team_id),
        "role": "admin",
    }
    assert response.headers["cache-control"] == "no-store"
    assert api.provider.created == [("julian@example.test", "Julián Torres", PASSWORD)]


async def test_a_confirmation_that_does_not_match_is_refused_before_anything_is_created(api):
    response = await post(
        api, "activate", token=TOKEN, password=PASSWORD, confirmation="something else"
    )

    assert response.status_code == 422 and response.json()["code"] == "password_mismatch"
    assert api.provider.created == []


async def test_a_password_the_policy_refuses_says_why_and_the_link_stays_valid(api):
    api.provider.refuse_password("min_length")

    response = await post(api, "activate", token=TOKEN, password="short", confirmation="short")

    assert response.status_code == 422
    assert response.json() == {
        "code": "password_policy",
        "detail": "password policy",
        "reasons": ["min_length"],
    }
    assert (await post(api, "status", token=TOKEN)).status_code == 200


async def test_a_link_cannot_be_activated_twice(api):
    await post(api, "activate", token=TOKEN, password=PASSWORD, confirmation=PASSWORD)

    response = await post(api, "activate", token=TOKEN, password=PASSWORD, confirmation=PASSWORD)

    assert response.status_code == 410 and response.json()["code"] == "invitation_used"
    assert len(api.provider.created) == 1


async def test_an_expired_link_cannot_be_activated(api):
    api.clock.advance(days=8)

    response = await post(api, "activate", token=TOKEN, password=PASSWORD, confirmation=PASSWORD)

    assert response.status_code == 410 and response.json()["code"] == "invitation_expired"


async def test_an_unknown_link_cannot_be_activated(api):
    response = await post(api, "activate", token="Z" * 43, password=PASSWORD, confirmation=PASSWORD)

    assert response.status_code == 404 and response.json()["code"] == "invitation_not_found"


async def test_an_email_that_already_has_an_account_is_a_conflict(api):
    api.provider.already_has_the_account()

    response = await post(api, "activate", token=TOKEN, password=PASSWORD, confirmation=PASSWORD)

    assert response.status_code == 409 and response.json()["code"] == "account_already_exists"


async def test_when_keycloak_is_down_the_answer_says_so(api):
    api.provider.be_down()

    response = await post(api, "activate", token=TOKEN, password=PASSWORD, confirmation=PASSWORD)

    assert (
        response.status_code == 503 and response.json()["code"] == "identity_provider_unavailable"
    )


async def test_an_error_never_echoes_the_token_the_password_or_the_person(api):
    api.provider.refuse_password("min_length")
    api.clock.advance(days=8)

    bodies = [
        (await post(api, "activate", token=TOKEN, password=PASSWORD, confirmation=PASSWORD)).text,
        (await post(api, "activate", token=TOKEN, password=PASSWORD, confirmation="x")).text,
        (await post(api, "status", token=TOKEN)).text,
    ]

    for body in bodies:
        assert TOKEN not in body and PASSWORD not in body and "julian" not in body.lower()


# ----------------------------------------------------------------- request new --
async def test_asking_for_a_new_invitation_tells_the_admins(api):
    api.clock.advance(days=8)

    response = await post(api, "request-new", token=TOKEN)

    assert response.status_code == 202 and response.json() == {"status": "requested"}
    assert [m.to for m in api.mailer.sent] == ["diego@example.test"]


async def test_there_is_nothing_to_request_while_the_link_works(api):
    response = await post(api, "request-new", token=TOKEN)

    assert response.status_code == 409 and response.json()["code"] == "invitation_still_valid"
    assert api.mailer.sent == []


async def test_a_new_invitation_cannot_be_requested_with_an_unknown_link(api):
    response = await post(api, "request-new", token="Z" * 43)

    assert response.status_code == 404


async def test_if_the_admins_cannot_be_emailed_the_answer_says_so(api):
    api.clock.advance(days=8)
    api.mailer.fail = True

    response = await post(api, "request-new", token=TOKEN)

    assert response.status_code == 502 and response.json()["code"] == "mail_unavailable"


# ---------------------------------------------------------------------- contract --
async def test_the_specification_documents_the_three_operations_and_their_errors(api):
    async with api.client() as client:
        spec = (await client.get("/openapi.json")).json()

    for path, errors in {
        "/v1/invitations/status": {"404", "410"},
        "/v1/invitations/activate": {"404", "409", "410", "422", "503"},
        "/v1/invitations/request-new": {"404", "409", "502"},
    }.items():
        operation = spec["paths"][path]["post"]
        assert errors <= set(operation["responses"]), path
    assert "ErrorResponse" in spec["components"]["schemas"]


# ------------------------------------------------- invite to a team (HU-06) --
TOKEN_ANA = "token-of-ana"
TOKEN_BRUNO = "token-of-bruno"
TOKEN_CARLA = "token-of-carla"


class TeamInvitations:
    """Ana is admin of Atlas and Carla one of its members; Bruno has no team."""

    def __init__(self) -> None:
        self.ana, self.bruno, self.carla = next_id(), next_id(), next_id()
        self.atlas = next_id()
        self.ana_membership = next_id()
        self.uow = FakeIdentityUnitOfWork()
        self.mailer = FakeMailer()
        clock = FakeClock()
        contacts = FakeTeamContactsDirectory({self.atlas: TeamContactsBuilder().build()})
        issue = IssueInvitationHandler(
            self.uow.factory(),
            FakeTokenGenerator(TOKEN),
            FakeRenderer(),
            self.mailer,
            clock,
            "https://app.test/activate",
        )
        handler = InviteToTeamHandler(
            self.uow.factory(),
            contacts,
            issue,
            FakeRenderer(),
            self.mailer,
            clock,
            "https://app.test/teams",
        )
        access = FakeTeamAccess(
            {(self.atlas, self.ana): TeamRole.ADMIN, (self.atlas, self.carla): TeamRole.MEMBER},
            membership_ids={(self.atlas, self.ana): self.ana_membership},
        )
        users = FakeAuthenticatedUsers(
            {TOKEN_ANA: self.ana, TOKEN_BRUNO: self.bruno, TOKEN_CARLA: self.carla}
        )
        app = create_app()
        app.dependency_overrides[deps.get_invite_to_team_handler] = _returning(handler)
        app.dependency_overrides[get_authenticated_users] = _returning(users)
        app.dependency_overrides[get_team_access] = _returning(access)
        self.app = app

    async def invite(self, token: str | None = TOKEN_ANA, team_id=None, **body):
        body = {"full_name": "Julián Torres", "email": "julian@example.test", **body}
        headers = {} if token is None else {"Authorization": f"Bearer {token}"}
        async with AsyncClient(
            transport=ASGITransport(app=self.app), base_url="http://tests"
        ) as client:
            return await client.post(
                f"/v1/teams/{team_id or self.atlas}/invitations", json=body, headers=headers
            )


@pytest.fixture
def invitations() -> TeamInvitations:
    return TeamInvitations()


async def test_an_admin_invites_someone_without_account_and_the_link_is_emailed(invitations):
    response = await invitations.invite()

    assert response.status_code == 201
    assert response.json() == {"outcome": "invitation_sent"}
    [invitation] = invitations.uow.invitations.by_id.values()
    assert invitation.role is TeamRole.MEMBER and invitation.status is InvitationStatus.PENDING
    assert invitation.created_by == invitations.ana_membership
    assert (
        f"activation_url=https://app.test/activate#t={TOKEN}"
        in invitations.mailer.sent[0].text_body
    )


async def test_the_role_can_be_chosen_in_the_body(invitations):
    await invitations.invite(role="admin")

    [invitation] = invitations.uow.invitations.by_id.values()
    assert invitation.role is TeamRole.ADMIN


async def test_inviting_an_existing_account_answers_member_added(invitations):
    await AppUserBuilder().with_email("julian@example.test").saved_in(invitations.uow.users)

    response = await invitations.invite()

    assert response.status_code == 201 and response.json() == {"outcome": "member_added"}
    assert invitations.uow.invitations.by_id == {}
    assert invitations.mailer.sent[0].subject == "member_added:es"


async def test_inviting_a_current_member_answers_409_already_a_team_member(invitations):
    await AppUserBuilder().with_email("julian@example.test").saved_in(invitations.uow.users)
    invitations.uow.team_membership.fail_with = AlreadyTeamMemberError("already in the team")

    response = await invitations.invite()

    assert response.status_code == 409
    assert response.json() == {"code": "already_a_team_member", "detail": "already a team member"}
    assert invitations.mailer.sent == []


async def test_inviting_a_disabled_account_answers_409_account_disabled(invitations):
    account = AppUserBuilder().with_email("julian@example.test").disabled()
    await account.saved_in(invitations.uow.users)

    response = await invitations.invite()

    assert response.status_code == 409 and response.json()["code"] == "account_disabled"


@pytest.mark.parametrize(
    ("body", "code"),
    [({"email": "not-an-email"}, "invalid_email"), ({"full_name": "   "}, "invalid_full_name")],
)
async def test_invalid_data_answers_422_with_its_code(invitations, body, code):
    response = await invitations.invite(**body)

    assert response.status_code == 422 and response.json()["code"] == code
    assert invitations.mailer.sent == []


@pytest.mark.parametrize(
    "body", [{"role": "owner"}, {"team_id": "x"}, {"created_by": "x"}, {"email": None}]
)
async def test_a_malformed_body_answers_422_and_invites_nobody(invitations, body):
    response = await invitations.invite(**body)

    assert response.status_code == 422
    assert invitations.uow.invitations.by_id == {} and invitations.mailer.sent == []


async def test_if_the_email_cannot_be_sent_the_answer_is_502_and_nothing_is_stored(invitations):
    invitations.mailer.fail = True

    response = await invitations.invite()

    assert response.status_code == 502 and response.json()["code"] == "mail_unavailable"
    assert invitations.uow.commits == 0


async def test_a_member_who_is_not_an_admin_gets_403_not_a_team_admin(invitations):
    response = await invitations.invite(TOKEN_CARLA)

    assert response.status_code == 403 and response.json()["code"] == "not_a_team_admin"
    assert invitations.uow.invitations.by_id == {} and invitations.mailer.sent == []


async def test_someone_outside_the_team_gets_403_not_a_team_member(invitations):
    response = await invitations.invite(TOKEN_BRUNO)

    assert response.status_code == 403 and response.json()["code"] == "not_a_team_member"
    assert invitations.mailer.sent == []


@pytest.mark.parametrize("token", [None, "forged-token"])
async def test_without_a_valid_token_the_invitation_answers_401(invitations, token):
    response = await invitations.invite(token)

    assert response.status_code == 401 and response.json()["code"] == "not_authenticated"
    assert invitations.mailer.sent == []


async def test_the_specification_documents_the_team_invitation_and_its_errors(invitations):
    async with AsyncClient(
        transport=ASGITransport(app=invitations.app), base_url="http://tests"
    ) as client:
        spec = (await client.get("/openapi.json")).json()

    operation = spec["paths"]["/v1/teams/{team_id}/invitations"]["post"]
    assert {"201", "401", "403", "404", "409", "422", "502"} <= set(operation["responses"])
    request = spec["components"]["schemas"]["InviteToTeamRequest"]
    assert request["properties"]["role"]["default"] == "member"
    assert request["additionalProperties"] is False
