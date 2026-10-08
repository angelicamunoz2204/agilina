"""The users HTTP API (``/v1/users``), with in-memory doubles behind the use cases and the
access ports: the users of a team, one user, the caller as a member (HU-04, HU-06)."""

import logging

import pytest

from agilina_api.teams.application.dtos import TeamView
from agilina_shared.enums import Language, OperationMode, TeamRole
from tests.api.builders import NOW
from tests.api.unit.teams.presentation.http.support import (
    TOKEN_ANA,
    TOKEN_BRUNO,
    TOKEN_CARLA,
    Api,
)

JOINED = NOW.isoformat().replace("+00:00", "Z")


async def test_an_admin_lists_the_users_with_their_role_label_and_blockers(api):
    response = await api.users("GET", "", TOKEN_ANA)

    assert response.status_code == 200
    assert response.json() == {
        "roles": [
            {"role": "admin", "label": "scrum_master"},
            {"role": "member", "label": "member"},
        ],
        "users": [
            {
                "user_id": str(api.ana),
                "full_name": "Ana Gil",
                "email": "ana@example.test",
                "role": "admin",
                "label": "scrum_master",
                "joined_at": JOINED,
                "role_change_blocked_by": "last_admin",
                "removal_blocked_by": "last_admin",
            },
            {
                "user_id": str(api.carla),
                "full_name": "Carla Ruiz",
                "email": "carla@example.test",
                "role": "member",
                "label": "member",
                "joined_at": JOINED,
                "role_change_blocked_by": None,
                "removal_blocked_by": None,
            },
        ],
    }


async def test_with_a_sprint_in_progress_the_list_says_no_role_can_change(api):
    api.queries.teams_with_active_sprint.add(api.atlas)

    members = (await api.users("GET", "", TOKEN_ANA)).json()["users"]

    assert [m["role_change_blocked_by"] for m in members] == ["sprint_in_progress"] * 2
    assert [m["removal_blocked_by"] for m in members] == ["last_admin", None]


async def test_an_admin_changes_the_role_of_a_member(api):
    response = await api.users("PATCH", f"/{api.carla}", TOKEN_ANA, json={"role": "admin"})

    assert response.status_code == 204 and response.content == b""
    assert api.role_in_atlas(api.carla) is TeamRole.ADMIN
    assert api.members_uow.committed is True


async def test_the_admin_of_the_token_is_who_asked_for_a_role_change(api, caplog):
    with caplog.at_level(logging.INFO):
        await api.users("PATCH", f"/{api.carla}", TOKEN_ANA, json={"role": "admin"})

    assert f"user {api.ana} changed the role of user {api.carla}" in caplog.text


async def test_the_only_admin_cannot_demote_themselves_and_gets_409_last_admin(api):
    response = await api.users("PATCH", f"/{api.ana}", TOKEN_ANA, json={"role": "member"})

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "last_admin"
    assert api.role_in_atlas(api.ana) is TeamRole.ADMIN and api.members_uow.committed is False


async def test_with_a_sprint_in_progress_a_role_change_gets_409_sprint_in_progress(api):
    api.members_uow.active_sprints.teams_with_active_sprint.add(api.atlas)

    response = await api.users("PATCH", f"/{api.carla}", TOKEN_ANA, json={"role": "admin"})

    assert response.status_code == 409 and response.json()["error"]["code"] == "sprint_in_progress"
    assert api.role_in_atlas(api.carla) is TeamRole.MEMBER


async def test_changing_the_role_of_someone_outside_the_team_answers_404(api):
    response = await api.users("PATCH", f"/{api.bruno}", TOKEN_ANA, json={"role": "admin"})

    assert response.status_code == 404 and response.json()["error"]["code"] == "member_not_found"


@pytest.mark.parametrize(
    "body", [{}, {"role": "scrum_master"}, {"role": "admin", "team_id": "x"}, {"role": None}]
)
async def test_a_malformed_role_change_answers_422_and_changes_nothing(api, body):
    response = await api.users("PATCH", f"/{api.carla}", TOKEN_ANA, json=body)

    assert response.status_code == 422
    assert api.role_in_atlas(api.carla) is TeamRole.MEMBER and api.members_uow.committed is False


async def test_an_admin_removes_a_member(api):
    response = await api.users("DELETE", f"/{api.carla}", TOKEN_ANA)

    assert response.status_code == 204 and response.content == b""
    assert api.role_in_atlas(api.carla) is None and api.members_uow.committed is True


async def test_the_admin_of_the_token_is_who_asked_for_a_removal(api, caplog):
    with caplog.at_level(logging.INFO):
        await api.users("DELETE", f"/{api.carla}", TOKEN_ANA)

    assert f"user {api.ana} removed user {api.carla}" in caplog.text


async def test_a_sprint_in_progress_does_not_prevent_a_removal(api):
    api.members_uow.active_sprints.teams_with_active_sprint.add(api.atlas)

    response = await api.users("DELETE", f"/{api.carla}", TOKEN_ANA)

    assert response.status_code == 204 and api.role_in_atlas(api.carla) is None


async def test_the_only_admin_cannot_remove_themselves_and_gets_409_last_admin(api):
    response = await api.users("DELETE", f"/{api.ana}", TOKEN_ANA)

    assert response.status_code == 409 and response.json()["error"]["code"] == "last_admin"
    assert api.role_in_atlas(api.ana) is TeamRole.ADMIN


async def test_removing_someone_outside_the_team_answers_404(api):
    response = await api.users("DELETE", f"/{api.bruno}", TOKEN_ANA)

    assert response.status_code == 404 and response.json()["error"]["code"] == "member_not_found"


async def test_a_malformed_member_id_answers_422(api):
    response = await api.users("DELETE", "/not-a-uuid", TOKEN_ANA)

    assert response.status_code == 422


USER_ROUTES = [
    ("GET", "", {}),
    ("GET", "/{carla}", {}),
    ("PATCH", "/{carla}", {"json": {"role": "admin"}}),
    ("DELETE", "/{carla}", {}),
]


def _path(api: Api, path: str) -> str:
    return path.format(carla=api.carla)


@pytest.mark.parametrize(("method", "path", "kwargs"), USER_ROUTES)
async def test_a_member_who_is_not_an_admin_gets_403_not_a_team_admin(api, method, path, kwargs):
    response = await api.users(method, _path(api, path), TOKEN_CARLA, **kwargs)

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "not_a_team_admin"
    assert "Ana Gil" not in response.text
    assert api.role_in_atlas(api.carla) is TeamRole.MEMBER and api.members_uow.committed is False


@pytest.mark.parametrize("mode", list(OperationMode))
@pytest.mark.parametrize(("method", "path", "kwargs"), USER_ROUTES)
async def test_the_mode_of_the_team_changes_no_permission(api, mode, method, path, kwargs):
    """The label differs between the modes; who may do what does not (HU-04, criterion 6)."""
    api.queries.modes[api.atlas] = mode
    api.queries.views[api.atlas] = TeamView(
        team_id=api.atlas, name="Atlas", mode=mode, language=Language.EN
    )

    admin = await api.users(method, _path(api, path), TOKEN_ANA, **kwargs)
    member = await api.users(method, _path(api, path), TOKEN_CARLA, **kwargs)

    assert admin.status_code in (200, 204)
    assert member.status_code == 403 and member.json()["error"]["code"] == "not_a_team_admin"


@pytest.mark.parametrize(("method", "path", "kwargs"), USER_ROUTES)
async def test_someone_outside_the_team_gets_403_not_a_team_member(api, method, path, kwargs):
    response = await api.users(method, _path(api, path), TOKEN_BRUNO, **kwargs)

    assert response.status_code == 403 and response.json()["error"]["code"] == "not_a_team_member"
    assert api.role_in_atlas(api.carla) is TeamRole.MEMBER


@pytest.mark.parametrize(("method", "path", "kwargs"), USER_ROUTES)
async def test_admin_rights_in_one_team_do_not_reach_another(api, method, path, kwargs):
    """Ana is admin of Atlas but only a member of Boreal: Atlas' admin rights do not travel."""
    response = await api.users(method, _path(api, path), TOKEN_ANA, team=api.boreal, **kwargs)

    assert response.status_code == 403 and response.json()["error"]["code"] == "not_a_team_admin"


@pytest.mark.parametrize(("method", "path", "kwargs"), USER_ROUTES)
async def test_without_a_valid_token_the_member_routes_answer_401(api, method, path, kwargs):
    missing = await api.users(method, _path(api, path), **kwargs)
    forged = await api.users(method, _path(api, path), "forged-token", **kwargs)

    for response in (missing, forged):
        assert (
            response.status_code == 401 and response.json()["error"]["code"] == "not_authenticated"
        )
    assert api.role_in_atlas(api.carla) is TeamRole.MEMBER


async def test_the_openapi_documents_the_user_routes_and_their_errors(api):
    async with api.client() as client:
        spec = (await client.get("/openapi.json")).json()

    listing = spec["paths"]["/v1/users"]["get"]
    assert {"200", "401", "403", "422", "500"} <= set(listing["responses"])
    me = spec["paths"]["/v1/users/me"]["get"]
    assert {"200", "401", "403", "404", "422", "500"} <= set(me["responses"])
    user = spec["paths"]["/v1/users/{user_id}"]
    assert {"200", "401", "403", "404", "422", "500"} <= set(user["get"]["responses"])
    assert {"204", "401", "403", "404", "409", "422", "500"} <= set(user["patch"]["responses"])
    assert {"204", "401", "403", "404", "409", "422", "500"} <= set(user["delete"]["responses"])
    assert "`not_a_team_admin`" in user["patch"]["responses"]["403"]["description"]
    assert "`last_admin`" in user["delete"]["responses"]["409"]["description"]
    assert "`sprint_in_progress`" in user["patch"]["responses"]["409"]["description"]
    for operation in (listing, me, user["get"]):
        team_id = next(p for p in operation["parameters"] if p["name"] == "team_id")
        assert team_id["in"] == "query" and team_id["required"] is True
    blockers = spec["components"]["schemas"]["UserInTeamResponse"]["properties"]
    assert "`sprint_in_progress`" in blockers["role_change_blocked_by"]["description"]
    assert "/v1/teams/{team_id}/members" not in spec["paths"]


# ------------------------------------------------------------- one user and me --
async def test_an_admin_reads_one_user_of_the_team(api):
    response = await api.users("GET", f"/{api.carla}", TOKEN_ANA)

    assert response.status_code == 200
    assert response.json() == {
        "user_id": str(api.carla),
        "full_name": "Carla Ruiz",
        "email": "carla@example.test",
        "role": "member",
        "label": "member",
        "joined_at": JOINED,
        "role_change_blocked_by": None,
        "removal_blocked_by": None,
    }


async def test_reading_someone_outside_the_team_answers_404_member_not_found(api):
    response = await api.users("GET", f"/{api.bruno}", TOKEN_ANA)

    assert response.status_code == 404 and response.json()["error"]["code"] == "member_not_found"


async def test_reading_a_malformed_user_id_answers_422(api):
    response = await api.users("GET", "/not-a-uuid", TOKEN_ANA)

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "validation_error"


async def test_a_member_sees_only_themselves_in_me(api):
    response = await api.users("GET", "/me", TOKEN_CARLA)

    assert response.status_code == 200
    assert response.json() == {
        "user_id": str(api.carla),
        "full_name": "Carla Ruiz",
        "email": "carla@example.test",
        "role": "member",
        "label": "member",
        "joined_at": JOINED,
    }


@pytest.mark.parametrize(
    ("mode", "label"),
    [(OperationMode.SUPPORT, "scrum_master"), (OperationMode.AUTONOMOUS, "admin")],
)
async def test_me_labels_the_admin_with_the_mode_of_the_team(api, mode, label):
    api.queries.modes[api.atlas] = mode

    response = await api.users("GET", "/me", TOKEN_ANA)

    assert (response.json()["role"], response.json()["label"]) == ("admin", label)


async def test_me_is_not_read_as_a_user_id(api):
    response = await api.users("GET", "/me", TOKEN_ANA)

    assert response.status_code == 200 and response.json()["user_id"] == str(api.ana)


async def test_someone_outside_the_team_gets_403_in_me(api):
    response = await api.users("GET", "/me", TOKEN_BRUNO)

    assert response.status_code == 403 and response.json()["error"]["code"] == "not_a_team_member"


async def test_without_a_token_me_answers_401(api):
    response = await api.users("GET", "/me")

    assert response.status_code == 401 and response.json()["error"]["code"] == "not_authenticated"


async def test_a_member_of_a_team_that_has_no_record_of_them_gets_404_in_me(api):
    """Only a race gets here: the access check saw the membership and the read does not."""
    api.queries.members[api.atlas] = ()

    response = await api.users("GET", "/me", TOKEN_ANA)

    assert response.status_code == 404 and response.json()["error"]["code"] == "member_not_found"


# ------------------------------------------------------------- the team in the query --
@pytest.mark.parametrize(("method", "path", "kwargs"), [("GET", "/me", {}), *USER_ROUTES])
async def test_a_request_without_the_team_answers_422_naming_the_field(api, method, path, kwargs):
    response = await api.users(method, _path(api, path), TOKEN_ANA, team="", **kwargs)

    assert response.status_code == 422
    fields = response.json()["error"]["details"]["fields"]
    assert {"field": "query.team_id", "reason": "missing"} in fields


async def test_a_malformed_team_answers_422(api):
    response = await api.users("GET", "", TOKEN_ANA, team="not-a-uuid")

    assert response.status_code == 422


async def test_a_team_that_does_not_exist_answers_403_like_a_foreign_one(api):
    from tests.api.builders import next_id

    response = await api.users("GET", "", TOKEN_ANA, team=next_id())

    assert response.status_code == 403 and response.json()["error"]["code"] == "not_a_team_member"


@pytest.mark.parametrize(
    ("method", "path"),
    [
        ("GET", "/{atlas}/members"),
        ("PATCH", "/{atlas}/members/{carla}"),
        ("DELETE", "/{atlas}/members/{carla}"),
        ("POST", "/{atlas}/invitations"),
    ],
)
async def test_the_old_routes_under_teams_no_longer_exist(api, method, path):
    url = path.format(atlas=api.atlas, carla=api.carla)

    response = await api.request(method, url, TOKEN_ANA)

    assert response.status_code in (404, 405)
    assert response.json()["error"]["code"] in {"not_found", "method_not_allowed"}
