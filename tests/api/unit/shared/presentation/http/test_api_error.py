"""The catalogs: a code is unique, snake_case, an error status and has a message."""

import re

import pytest

from agilina_api.identity.presentation.http.errors import IdentityErrors
from agilina_api.shared.presentation.http.api_error import (
    ApiError,
    ApiException,
    SharedErrors,
    catalog_of,
)
from agilina_api.shared.presentation.http.error_schema import errors_of
from agilina_api.teams.presentation.http.errors import TeamsErrors

ALL = (*catalog_of(SharedErrors), *catalog_of(IdentityErrors), *catalog_of(TeamsErrors))


def test_the_catalogs_are_not_empty():
    assert len(ALL) >= 20


def test_every_code_is_unique_across_all_catalogs():
    codes = [error.code for error in ALL]

    assert len(codes) == len(set(codes))


@pytest.mark.parametrize("error", ALL, ids=lambda error: error.code)
def test_every_entry_is_well_formed(error: ApiError):
    assert re.fullmatch(r"[a-z]+(_[a-z]+)*", error.code)
    assert 400 <= error.status <= 599
    assert error.message.endswith(".") and error.message[0].isupper()


def test_an_api_exception_carries_its_entry_and_details():
    exception = ApiException(SharedErrors.VALIDATION, {"fields": []})

    assert exception.error is SharedErrors.VALIDATION and exception.details == {"fields": []}


def test_errors_of_groups_the_codes_of_a_status_for_the_openapi_document():
    responses = errors_of(
        IdentityErrors.INVITATION_USED, IdentityErrors.INVITATION_EXPIRED, SharedErrors.VALIDATION
    )

    # The 500 is always there: every endpoint can fail in a way nobody planned for.
    assert set(responses) == {410, 422, 500}
    assert "`internal_error`" in responses[500]["description"]
    assert "`invitation_used`" in responses[410]["description"]
    assert "`invitation_expired`" in responses[410]["description"]


def test_errors_of_does_not_list_the_same_error_twice():
    responses = errors_of(SharedErrors.INTERNAL, SharedErrors.INTERNAL)

    assert responses[500]["description"].count("`internal_error`") == 1
