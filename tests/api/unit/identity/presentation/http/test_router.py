"""The invitations HTTP API, with in-memory doubles behind the use cases (no database)."""

import pytest
from httpx import ASGITransport, AsyncClient

from agilina_api.bootstrap.app import create_app
from agilina_api.identity.application.commands.activate_account import ActivateAccountHandler
from agilina_api.identity.application.commands.request_new_invitation import (
    RequestNewInvitationHandler,
)
from agilina_api.identity.application.queries.get_invitation_status import (
    GetInvitationStatusHandler,
)
from agilina_api.identity.presentation.http import dependencies as deps
from tests.api.builders import (
    PASSWORD,
    TOKEN,
    ContactBuilder,
    InvitationBuilder,
    TeamContactsBuilder,
    next_id,
)
from tests.api.doubles import (
    FakeClock,
    FakeIdentityProvider,
    FakeIdentityUnitOfWork,
    FakeInvitationQueries,
    FakeMailer,
    FakeRenderer,
    FakeTeamContactsDirectory,
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

    assert response.status_code == 410 and response.json()["error"]["code"] == "invitation_used"


async def test_an_expired_link_is_gone_with_its_own_code(api):
    api.clock.advance(days=8)

    response = await post(api, "status", token=TOKEN)

    assert response.status_code == 410 and response.json()["error"]["code"] == "invitation_expired"


@pytest.mark.parametrize("token", ["", "short", "Z" * 43, "x" * 300])
async def test_an_altered_or_unknown_link_is_not_found(api, token):
    response = await post(api, "status", token=token)

    assert response.status_code in (404, 422)  # 422: too long for the schema, still not a link
    if response.status_code == 404:
        assert response.json()["error"]["code"] == "invitation_not_found"


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

    assert response.status_code == 422 and response.json()["error"]["code"] == "password_mismatch"
    assert api.provider.created == []


async def test_a_password_the_policy_refuses_says_why_and_the_link_stays_valid(api):
    api.provider.refuse_password("min_length")

    response = await post(api, "activate", token=TOKEN, password="short", confirmation="short")

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "password_policy"
    assert response.json()["error"]["details"] == {"reasons": ["min_length"]}
    assert (await post(api, "status", token=TOKEN)).status_code == 200


async def test_a_link_cannot_be_activated_twice(api):
    await post(api, "activate", token=TOKEN, password=PASSWORD, confirmation=PASSWORD)

    response = await post(api, "activate", token=TOKEN, password=PASSWORD, confirmation=PASSWORD)

    assert response.status_code == 410 and response.json()["error"]["code"] == "invitation_used"
    assert len(api.provider.created) == 1


async def test_an_expired_link_cannot_be_activated(api):
    api.clock.advance(days=8)

    response = await post(api, "activate", token=TOKEN, password=PASSWORD, confirmation=PASSWORD)

    assert response.status_code == 410 and response.json()["error"]["code"] == "invitation_expired"


async def test_an_unknown_link_cannot_be_activated(api):
    response = await post(api, "activate", token="Z" * 43, password=PASSWORD, confirmation=PASSWORD)

    assert (
        response.status_code == 404 and response.json()["error"]["code"] == "invitation_not_found"
    )


async def test_an_email_that_already_has_an_account_is_a_conflict(api):
    api.provider.already_has_the_account()

    response = await post(api, "activate", token=TOKEN, password=PASSWORD, confirmation=PASSWORD)

    assert (
        response.status_code == 409 and response.json()["error"]["code"] == "account_already_exists"
    )


async def test_when_keycloak_is_down_the_answer_says_so(api):
    api.provider.be_down()

    response = await post(api, "activate", token=TOKEN, password=PASSWORD, confirmation=PASSWORD)

    assert (
        response.status_code == 503
        and response.json()["error"]["code"] == "identity_provider_unavailable"
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

    assert (
        response.status_code == 409 and response.json()["error"]["code"] == "invitation_still_valid"
    )
    assert api.mailer.sent == []


async def test_a_new_invitation_cannot_be_requested_with_an_unknown_link(api):
    response = await post(api, "request-new", token="Z" * 43)

    assert response.status_code == 404


async def test_if_the_admins_cannot_be_emailed_the_answer_says_so(api):
    api.clock.advance(days=8)
    api.mailer.fail = True

    response = await post(api, "request-new", token=TOKEN)

    assert response.status_code == 502 and response.json()["error"]["code"] == "mail_unavailable"


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
    assert "ErrorEnvelope" in spec["components"]["schemas"]
